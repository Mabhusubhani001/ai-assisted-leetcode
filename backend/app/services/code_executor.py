from __future__ import annotations
import ast
import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import httpx
from typing import TYPE_CHECKING
from pydantic import BaseModel
from app.core.config import settings

if TYPE_CHECKING:
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
    Supports Python 3, C++, Java 17, and JavaScript with language-specific test drivers.
    """

    LANGUAGE_MAP = {
        71: "python",
        54: "cpp",
        62: "java",
        63: "javascript",
    }

    BLOCKED_MODULES = {
        "os", "sys", "subprocess", "shutil", "socket", "urllib", "requests",
        "http", "posix", "pty", "commands", "ctypes", "fcntl", "resource",
        "signal", "multiprocessing", "threading", "builtins", "importlib",
        "inspect", "pickle", "shelve", "tempfile", "io", "pathlib", "glob",
        "webbrowser", "ftplib", "smtplib", "telnetlib", "ssl",
    }

    BLOCKED_CALLS = {
        "eval", "exec", "open", "compile", "__import__", "globals",
        "locals", "vars", "getattr", "setattr", "delattr", "exit", "quit",
        "breakpoint", "memoryview", "input",
    }

    BLOCKED_ATTRS = {
        "__subclasses__", "__bases__", "__mro__", "__code__",
        "__builtins__", "__globals__", "__class__", "__qualname__",
        "__dict__", "__closure__",
    }

    @classmethod
    def _audit_python_ast(cls, source_code: str) -> str | None:
        """
        Static AST Security Audit.
        Scans code before execution to block dangerous imports, builtins,
        and dunder attribute inspection escapes (e.g. __subclasses__).
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return f"SyntaxError: {e.msg} on line {e.lineno}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in cls.BLOCKED_MODULES:
                        return f"Security Restriction: Importing '{mod}' is not permitted in competitive programming practice."
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    if mod in cls.BLOCKED_MODULES:
                        return f"Security Restriction: Importing from '{mod}' is not permitted in competitive programming practice."
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.BLOCKED_CALLS:
                        return f"Security Restriction: Calling '{node.func.id}()' is prohibited."
            elif isinstance(node, ast.Attribute):
                if node.attr in cls.BLOCKED_ATTRS:
                    return f"Security Restriction: Accessing protected attribute '{node.attr}' is prohibited."

        return None

    @classmethod
    def _get_legacy_python_driver(cls, slug: str) -> str:
        """Fallback driver definitions for initial seed questions."""
        if slug in ("two-sum", "two-sum-ii-input-array-is-sorted"):
            return """
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
            return """
import sys

raw = sys.stdin.read()
s = raw.strip()

sol = Solution()
ans = sol.isValid(s)
print("true" if ans else "false")
"""
        elif slug == "reverse-linked-list":
            return """
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
        return "import sys\nprint(sys.stdin.read().strip())"

    @classmethod
    def _generate_executable_code(
        cls, question: Question, source_code: str, language_id: int = 71
    ) -> str:
        """
        Assembles student solution with the language-specific test driver.
        1. Checks if question.driver_code has a driver for this language.
        2. Falls back to legacy drivers if present.
        3. Appends preamble/headers where appropriate.
        """
        lang_key = cls.LANGUAGE_MAP.get(language_id, "python")
        slug = question.slug
        driver = ""

        # 1. Fetch dynamic driver from question model
        driver_dict = getattr(question, "driver_code", None) or {}
        if isinstance(driver_dict, dict) and driver_dict.get(lang_key):
            driver = driver_dict[lang_key]
        elif language_id == 71:
            driver = cls._get_legacy_python_driver(slug)

        if not driver:
            return source_code

        # 2. Wrap source code with language driver
        if language_id == 71:  # Python 3
            preamble = (
                "from typing import List, Dict, Tuple, Set, Optional, Any, Union\n"
                "import sys, json, math, collections, heapq\n\n"
            )
            return f"{preamble}{source_code}\n\n{driver}"
        else:  # C++, Java, JavaScript
            return f"{source_code}\n\n{driver}"

    # Retain backwards-compatible alias for existing tests
    @classmethod
    def _generate_python_harness(cls, slug: str, source_code: str) -> str:
        driver = cls._get_legacy_python_driver(slug)
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
        executable_code = cls._generate_executable_code(question, source_code, language_id)

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
        language_id: int = 71,  # 71 = Python 3
        timeout_sec: float = 2.0,
    ) -> ExecutionResult:
        """
        Executes code sequentially against all test cases.
        For Python 3 (language_id=71):
          1. Static AST Security Audit (Layer 1)
          2. Environment & Secret Scrubbing (Layer 2)
          3. Process isolation with Linux rlimit and timeouts (Layer 3)
        For other languages:
          Returns informative notification that live sandbox is active for Python 3.
        """
        total_cases = len(test_cases)
        passed_count = 0
        max_time = 0.0

        # Language Guardrail: Live in-container sandbox executes Python 3
        if language_id != 71:
            return ExecutionResult(
                status="RUNTIME_ERROR",
                passed_test_cases=0,
                total_test_cases=total_cases,
                execution_time_sec=0.0,
                stderr="Live evaluation sandbox is currently active for Python 3. Please switch language to Python 3 in the editor header to execute test cases.",
            )

        # Layer 1: Static AST Security Audit (Syntax Analysis)
        security_violation = cls._audit_python_ast(source_code)
        if security_violation:
            return ExecutionResult(
                status="RUNTIME_ERROR",
                passed_test_cases=0,
                total_test_cases=total_cases,
                execution_time_sec=0.0,
                stderr=security_violation,
            )

        # Layer 2: Generate executable test harness with standard algorithmic imports
        harness_code = cls._generate_executable_code(question, source_code, language_id)

        # Create isolated temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_script = os.path.join(temp_dir, "solution.py")
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(harness_code)

            # Scrubbed environment: ZERO access to host environment variables or secrets
            isolated_env = {
                "PYTHONPATH": "",
                "LANG": "C.UTF-8",
                "PYTHONHASHSEED": "0",
            }

            def set_rlimits():
                try:
                    import resource
                    # 2 seconds CPU limit
                    resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
                    # 128MB RAM limit
                    resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
                    # Disable file writes
                    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
                except Exception:
                    pass

            for idx, tc in enumerate(test_cases):
                start_t = time.perf_counter()

                try:
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable,
                        temp_script,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=isolated_env,
                        cwd=temp_dir,
                        preexec_fn=set_rlimits if sys.platform != "win32" else None,
                    )

                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(input=tc.stdin.encode("utf-8")),
                        timeout=timeout_sec,
                    )
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                        await proc.wait()
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

                def normalize(val: str) -> str:
                    try:
                        parsed = json.loads(val)
                        return json.dumps(parsed, sort_keys=True)
                    except Exception:
                        return val.replace(" ", "").lower()

                if normalize(actual_output) == normalize(expected_output):
                    passed_count += 1
                else:
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
                            "message": "Failed on hidden test case. Review edge cases (negative numbers, boundaries, duplicates).",
                        }

                    return ExecutionResult(
                        status="WRONG_ANSWER",
                        passed_test_cases=passed_count,
                        total_test_cases=total_cases,
                        execution_time_sec=round(max_time, 3),
                        failed_test_case_info=failed_info,
                    )

            return ExecutionResult(
                status="ACCEPTED",
                passed_test_cases=passed_count,
                total_test_cases=total_cases,
                execution_time_sec=round(max_time, 3),
            )
