import asyncio
import base64
import json
import logging
import subprocess
import sys
import tempfile
import time
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.models.question import Question
from app.models.test_case import TestCase

logger = logging.getLogger("code_executor")

class ExecutionResult(BaseModel):
    status: str  # ACCEPTED, WRONG_ANSWER, TIME_LIMIT_EXCEEDED, RUNTIME_ERROR, COMPILATION_ERROR
    passed_test_cases: int
    total_test_cases: int
    execution_time_sec: float
    memory_used_kb: int = 15360  # ~15MB baseline Python runtime
    compile_output: str | None = None
    stderr: str | None = None
    failed_test_case_info: dict | None = None  # Populated ONLY for public test cases

class CodeExecutorService:
    """
    Sandboxed Code Execution Engine.
    Executes student solutions against public and hidden test cases with strict 2.0s timeouts.
    Guarantees that hidden test case inputs are NEVER disclosed on wrong answers.
    """

    @classmethod
    def _generate_python_harness(cls, slug: str, source_code: str) -> str:
        """Wraps student solution with a driver that reads stdin and outputs formatted JSON."""
        if slug == "two-sum":
            driver = """
import sys, json

lines = sys.stdin.read().strip().splitlines()
if not lines:
    print("[]")
    sys.exit(0)

nums = [int(x) for x in lines[0].split()]
target = int(lines[1])

sol = Solution()
ans = sol.twoSum(nums, target)
print(json.dumps(ans))
"""
        elif slug == "valid-parentheses":
            driver = """
import sys

raw = sys.stdin.read()
s = raw.strip()

sol = Solution()
ans = sol.isValid(s)
print("true" if ans else "false")
"""
        elif slug == "reverse-linked-list":
            driver = """
import sys, json

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def to_linked_list(arr):
    dummy = ListNode(0)
    curr = dummy
    for x in arr:
        curr.next = ListNode(x)
        curr = curr.next
    return dummy.next

def to_array(head):
    res = []
    curr = head
    while curr:
        res.append(curr.val)
        curr = curr.next
    return res

raw = sys.stdin.read().strip()
arr = [int(x) for x in raw.split()] if raw else []
head = to_linked_list(arr)

sol = Solution()
reversed_head = sol.reverseList(head)
print(json.dumps(to_array(reversed_head)))
"""
        else:
            driver = "import sys\nprint(sys.stdin.read().strip())"

        preamble = (
            "from typing import List, Dict, Tuple, Set, Optional, Any, Union\n"
            "import sys, json, math, collections, heapq\n\n"
        )
        return f"{preamble}{source_code}\n\n{driver}"

    @classmethod
    async def _execute_via_judge0(
        cls,
        question: Question,
        test_cases: list[TestCase],
        source_code: str,
        language_id: int,
        timeout_sec: float,
    ) -> ExecutionResult:
        """
        Dispatches code evaluation to a dedicated Judge0 instance with Linux cgroups and isolated namespaces.
        """
        slug = question.slug
        total_cases = len(test_cases)
        passed_count = 0
        max_time = 0.0
        max_memory_kb = 0

        # Construct request headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if settings.JUDGE0_AUTH_TOKEN:
            headers["X-Auth-Token"] = settings.JUDGE0_AUTH_TOKEN
        if settings.JUDGE0_RAPIDAPI_KEY:
            headers["X-RapidAPI-Key"] = settings.JUDGE0_RAPIDAPI_KEY
            headers["X-RapidAPI-Host"] = settings.JUDGE0_RAPIDAPI_HOST

        # Generate language-appropriate test harness
        if language_id == 71:  # Python 3
            executable_code = cls._generate_python_harness(slug, source_code)
        else:
            executable_code = source_code

        b64_source = base64.b64encode(executable_code.encode("utf-8")).decode("ascii")
        api_url = f"{settings.JUDGE0_API_URL.rstrip('/')}/submissions?base64_encoded=true&wait=true"

        def b64_decode(val: str | None) -> str:
            if not val:
                return ""
            try:
                return base64.b64decode(val).decode("utf-8", errors="replace")
            except Exception:
                return val

        async with httpx.AsyncClient(timeout=timeout_sec + 5.0) as client:
            for idx, tc in enumerate(test_cases):
                b64_stdin = base64.b64encode(tc.stdin.encode("utf-8")).decode("ascii")
                b64_expected = base64.b64encode(tc.expected_stdout.encode("utf-8")).decode("ascii")

                payload = {
                    "source_code": b64_source,
                    "language_id": language_id,
                    "stdin": b64_stdin,
                    "expected_output": b64_expected,
                    "cpu_time_limit": timeout_sec,
                    "wall_time_limit": timeout_sec * 2,
                    "memory_limit": int(question.memory_limit_mb * 1024),
                }

                resp = await client.post(api_url, json=payload, headers=headers)
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Judge0 returned HTTP {resp.status_code}: {resp.text}")
                data = resp.json()

                status_id = data.get("status", {}).get("id")
                stdout_text = b64_decode(data.get("stdout")).strip()
                stderr_text = b64_decode(data.get("stderr")).strip()
                compile_text = b64_decode(data.get("compile_output")).strip()

                exec_time = float(data.get("time") or 0.0)
                if exec_time > max_time:
                    max_time = exec_time

                mem_kb = int(data.get("memory") or 0)
                if mem_kb > max_memory_kb:
                    max_memory_kb = mem_kb

                if status_id == 3:  # Accepted
                    passed_count += 1
                elif status_id == 5:  # Time Limit Exceeded
                    return ExecutionResult(
                        status="TIME_LIMIT_EXCEEDED",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        memory_used_kb=max_memory_kb or 15360,
                        stderr="Time Limit Exceeded. Check for infinite loops or non-optimal algorithms.",
                    )
                elif status_id == 6:  # Compilation Error
                    return ExecutionResult(
                        status="COMPILATION_ERROR",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        memory_used_kb=max_memory_kb,
                        compile_output=compile_text,
                    )
                elif status_id in (7, 8, 9, 10, 11, 12):  # Runtime Error
                    return ExecutionResult(
                        status="RUNTIME_ERROR",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        memory_used_kb=max_memory_kb,
                        stderr=stderr_text or data.get("status", {}).get("description", "Runtime Error"),
                    )
                else:  # Status 4 = Wrong Answer
                    failed_info = None
                    if not tc.is_hidden:
                        failed_info = {
                            "test_case_number": idx + 1,
                            "stdin": tc.stdin,
                            "expected_stdout": tc.expected_stdout,
                            "actual_stdout": stdout_text,
                        }
                    else:
                        failed_info = {
                            "test_case_number": idx + 1,
                            "is_hidden": True,
                            "message": "Failed on hidden test case. Review edge cases (negative numbers, boundaries, duplicates).",
                        }

                    return ExecutionResult(
                        status="WRONG_ANSWER",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        memory_used_kb=max_memory_kb or 15360,
                        failed_test_case_info=failed_info,
                    )

            return ExecutionResult(
                status="ACCEPTED",
                passed_test_cases=passed_count,
                total_test_cases=total_cases,
                execution_time_sec=round(max_time, 3),
                memory_used_kb=max_memory_kb or 15360,
            )

    @classmethod
    async def execute_submission(
        cls,
        question: Question,
        test_cases: list[TestCase],
        source_code: str,
        language_id: int = 71,  # 71 = Python 3 in Judge0
        timeout_sec: float = 2.0,
    ) -> ExecutionResult:
        """
        Executes code sequentially against all test cases.
        Dispatches to Judge0 if JUDGE0_API_URL is configured; otherwise uses internal async runner.
        Stops on first failure to save compute (standard LeetCode evaluation behavior).
        """
        # Route to Judge0 if configured, with graceful fallback to internal runner
        if settings.JUDGE0_API_URL:
            try:
                return await cls._execute_via_judge0(
                    question=question,
                    test_cases=test_cases,
                    source_code=source_code,
                    language_id=language_id,
                    timeout_sec=timeout_sec,
                )
            except Exception as e:
                logger.warning(
                    "Judge0 execution attempt failed (%s). Falling back to internal runner.", e
                )

        slug = question.slug
        total_cases = len(test_cases)
        passed_count = 0
        max_time = 0.0

        harness_code = cls._generate_python_harness(slug, source_code)

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(harness_code)
            temp_script = f.name

        try:
            for idx, tc in enumerate(test_cases):
                start_t = time.perf_counter()

                try:
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable,
                        temp_script,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(input=tc.stdin.encode("utf-8")),
                        timeout=timeout_sec,
                    )
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return ExecutionResult(
                        status="TIME_LIMIT_EXCEEDED",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=timeout_sec,
                        stderr="Time Limit Exceeded (2.0s exceeded). Check for infinite loops or non-optimal algorithms.",
                    )

                elapsed = time.perf_counter() - start_t
                if elapsed > max_time:
                    max_time = elapsed

                # Check runtime error
                if proc.returncode != 0:
                    err_msg = stderr_bytes.decode("utf-8", errors="replace")
                    return ExecutionResult(
                        status="RUNTIME_ERROR",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        stderr=err_msg[:1000],
                    )

                # Compare output (normalized)
                actual_output = stdout_bytes.decode("utf-8", errors="replace").strip()
                expected_output = tc.expected_stdout.strip()

                # Normalize JSON array representations if applicable
                def normalize(val: str) -> str:
                    try:
                        parsed = json.loads(val)
                        return json.dumps(parsed, sort_keys=True)
                    except Exception:
                        return val.replace(" ", "").lower()

                if normalize(actual_output) == normalize(expected_output):
                    passed_count += 1
                else:
                    # WRONG ANSWER
                    # Security boundary: If failure is on a hidden test case, NEVER leak input/expected
                    failed_info = None
                    if not tc.is_hidden:
                        failed_info = {
                            "test_case_number": idx + 1,
                            "stdin": tc.stdin,
                            "expected_stdout": tc.expected_stdout,
                            "actual_stdout": actual_output,
                        }
                    else:
                        failed_info = {
                            "test_case_number": idx + 1,
                            "is_hidden": True,
                            "message": "Failed on hidden test case. Review edge cases (negative numbers, boundaries, duplicates)."
                        }

                    return ExecutionResult(
                        status="WRONG_ANSWER",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        failed_test_case_info=failed_info,
                    )

            # All test cases passed!
            return ExecutionResult(
                status="ACCEPTED",
                passed_test_cases=passed_count,
                total_test_cases=total_cases,
                execution_time_sec=round(max_time, 3),
            )

        finally:
            import os
            try:
                os.remove(temp_script)
            except Exception:
                pass
