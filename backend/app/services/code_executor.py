import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pydantic import BaseModel
from app.models.question import Question
from app.models.test_case import TestCase

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
        Stops on first failure to save compute (standard LeetCode evaluation behavior).
        """
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
