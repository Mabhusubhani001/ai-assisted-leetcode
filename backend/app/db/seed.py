import asyncio
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.question import Question
from app.models.test_case import TestCase

# ==============================================================================
# Comprehensive DSA Problem Seeds with 2-3 Public & Many Hidden Test Cases
# ==============================================================================

SEED_QUESTIONS = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "easy",
        "description": """# Two Sum

Given an array of integers `nums` and an integer `target`, return **indices of the two numbers** such that they add up to `target`.

You may assume that each input would have **exactly one solution**, and you may not use the same element twice.

You can return the answer in any order.

### Example 1:
```text
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

### Example 2:
```text
Input: nums = [3,2,4], target = 6
Output: [1,2]
```

### Example 3:
```text
Input: nums = [3,3], target = 6
Output: [0,1]
```

### Constraints:
* `2 <= nums.length <= 10^4`
* `-10^9 <= nums[i] <= 10^9`
* `-10^9 <= target <= 10^9`
* **Only one valid answer exists.**
""",
        "starter_code": {
            "python": "class Solution:\n    def twoSum(self, nums: list[int], target: int) -> list[int]:\n        pass\n",
            "cpp": "#include <vector>\n\nclass Solution {\npublic:\n    std::vector<int> twoSum(std::vector<int>& nums, int target) {\n        \n    }\n};\n",
            "java": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
            "javascript": "/**\n * @param {number[]} nums\n * @param {number} target\n * @return {number[]}\n */\nvar twoSum = function(nums, target) {\n    \n};\n"
        },
        "memory_limit_mb": 256,
        "time_limit_sec": 2.0,
        "is_published": True,
        "test_cases": [
            # 3 Public Test Cases (Visible in UI)
            {"stdin": "2 7 11 15\n9", "expected_stdout": "[0, 1]", "is_hidden": False},
            {"stdin": "3 2 4\n6", "expected_stdout": "[1, 2]", "is_hidden": False},
            {"stdin": "3 3\n6", "expected_stdout": "[0, 1]", "is_hidden": False},
            # 7 Hidden Test Cases (Edge Cases)
            {"stdin": "-1 -2 -3 -4 -5\n-8", "expected_stdout": "[2, 4]", "is_hidden": True},
            {"stdin": "-3 4 3 90\n0", "expected_stdout": "[0, 2]", "is_hidden": True},
            {"stdin": "1000000000 500000000 500000000\n1000000000", "expected_stdout": "[1, 2]", "is_hidden": True},
            {"stdin": "0 4 3 0\n0", "expected_stdout": "[0, 3]", "is_hidden": True},
            {"stdin": "1 5 8 13 19 25 30\n31", "expected_stdout": "[0, 6]", "is_hidden": True},
            {"stdin": "1 1 1 2 3 4 5\n9", "expected_stdout": "[5, 6]", "is_hidden": True},
            {"stdin": "2 5 5 11\n10", "expected_stdout": "[1, 2]", "is_hidden": True},
        ]
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "difficulty": "easy",
        "description": """# Valid Parentheses

Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

### Example 1:
```text
Input: s = "()"
Output: true
```

### Example 2:
```text
Input: s = "()[]{}"
Output: true
```

### Example 3:
```text
Input: s = "(]"
Output: false
```

### Constraints:
* `1 <= s.length <= 10^4`
* `s` consists of parentheses only `'()[]{}'`.
""",
        "starter_code": {
            "python": "class Solution:\n    def isValid(self, s: str) -> bool:\n        pass\n",
            "cpp": "#include <string>\n\nclass Solution {\npublic:\n    bool isValid(std::string s) {\n        \n    }\n};\n",
            "java": "class Solution {\n    public boolean isValid(String s) {\n        return false;\n    }\n}\n",
            "javascript": "/**\n * @param {string} s\n * @return {boolean}\n */\nvar isValid = function(s) {\n    \n};\n"
        },
        "memory_limit_mb": 256,
        "time_limit_sec": 2.0,
        "is_published": True,
        "test_cases": [
            # 3 Public Test Cases (Visible in UI)
            {"stdin": "()", "expected_stdout": "true", "is_hidden": False},
            {"stdin": "()[]{}", "expected_stdout": "true", "is_hidden": False},
            {"stdin": "(]", "expected_stdout": "false", "is_hidden": False},
            # 7 Hidden Test Cases (Edge Cases)
            {"stdin": "([{}])", "expected_stdout": "true", "is_hidden": True},
            {"stdin": "([)]", "expected_stdout": "false", "is_hidden": True},
            {"stdin": "[", "expected_stdout": "false", "is_hidden": True},
            {"stdin": "]", "expected_stdout": "false", "is_hidden": True},
            {"stdin": "({[", "expected_stdout": "false", "is_hidden": True},
            {"stdin": "{[()]()}[{}]", "expected_stdout": "true", "is_hidden": True},
            {"stdin": "()()}", "expected_stdout": "false", "is_hidden": True},
        ]
    },
    {
        "title": "Reverse Linked List",
        "slug": "reverse-linked-list",
        "difficulty": "easy",
        "description": """# Reverse Linked List

Given the `head` of a singly linked list, reverse the list, and return **the reversed list**.

### Example 1:
```text
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]
```

### Example 2:
```text
Input: head = [1,2]
Output: [2,1]
```

### Example 3:
```text
Input: head = []
Output: []
```

### Constraints:
* The number of nodes in the list is the range `[0, 5000]`.
* `-5000 <= Node.val <= 5000`

**Follow up:** A linked list can be reversed either iteratively or recursively. Could you implement both?
""",
        "starter_code": {
            "python": "# Definition for singly-linked list.\n# class ListNode:\n#     def __init__(self, val=0, next=None):\n#         self.val = val\n#         self.next = next\nclass Solution:\n    def reverseList(self, head):\n        pass\n",
            "cpp": "/**\n * Definition for singly-linked list.\n * struct ListNode {\n *     int val;\n *     ListNode *next;\n *     ListNode() : val(0), next(nullptr) {}\n *     ListNode(int x) : val(x), next(nullptr) {}\n *     ListNode(int x, ListNode *next) : val(x), next(next) {}\n * };\n */\nclass Solution {\npublic:\n    ListNode* reverseList(ListNode* head) {\n        \n    }\n};\n",
            "java": "class Solution {\n    public ListNode reverseList(ListNode head) {\n        return null;\n    }\n}\n",
            "javascript": "/**\n * Definition for singly-linked list.\n * function ListNode(val, next) {\n *     this.val = (val===undefined ? 0 : val)\n *     this.next = (next===undefined ? null : next)\n * }\n */\n/**\n * @param {ListNode} head\n * @return {ListNode}\n */\nvar reverseList = function(head) {\n    \n};\n"
        },
        "memory_limit_mb": 256,
        "time_limit_sec": 2.0,
        "is_published": True,
        "test_cases": [
            # 3 Public Test Cases (Visible in UI)
            {"stdin": "1 2 3 4 5", "expected_stdout": "[5, 4, 3, 2, 1]", "is_hidden": False},
            {"stdin": "1 2", "expected_stdout": "[2, 1]", "is_hidden": False},
            {"stdin": "", "expected_stdout": "[]", "is_hidden": False},
            # 7 Hidden Test Cases (Edge Cases)
            {"stdin": "42", "expected_stdout": "[42]", "is_hidden": True},
            {"stdin": "1 1", "expected_stdout": "[1, 1]", "is_hidden": True},
            {"stdin": "1 2 1 2", "expected_stdout": "[2, 1, 2, 1]", "is_hidden": True},
            {"stdin": "5 4 3 2 1", "expected_stdout": "[1, 2, 3, 4, 5]", "is_hidden": True},
            {"stdin": "-1 -2 -3", "expected_stdout": "[-3, -2, -1]", "is_hidden": True},
            {"stdin": "10 20 30 40 50 60 70 80 90 100", "expected_stdout": "[100, 90, 80, 70, 60, 50, 40, 30, 20, 10]", "is_hidden": True},
            {"stdin": "0 0 0", "expected_stdout": "[0, 0, 0]", "is_hidden": True},
        ]
    }
]

async def seed_database():
    """Idempotently seeds baseline DSA questions and test cases."""
    print("🌱 Starting database seeding...")
    async with AsyncSessionLocal() as session:
        for q_data in SEED_QUESTIONS:
            slug = q_data["slug"]
            # Check if question exists
            existing_q = await session.scalar(select(Question).where(Question.slug == slug))

            if existing_q:
                print(f"  • Question '{slug}' already exists (ID: {existing_q.id}). Updating test cases...")
                question_id = existing_q.id
                # Clear existing test cases to re-seed cleanly
                await session.execute(delete(TestCase).where(TestCase.question_id == question_id))
            else:
                new_q = Question(
                    title=q_data["title"],
                    slug=slug,
                    difficulty=q_data["difficulty"],
                    description=q_data["description"],
                    starter_code=q_data["starter_code"],
                    memory_limit_mb=q_data["memory_limit_mb"],
                    time_limit_sec=q_data["time_limit_sec"],
                    is_published=q_data["is_published"]
                )
                session.add(new_q)
                await session.flush()
                question_id = new_q.id
                print(f"  • Inserted question '{slug}' (ID: {question_id})")

            # Insert test cases
            tc_list = []
            for tc in q_data["test_cases"]:
                tc_list.append(TestCase(
                    question_id=question_id,
                    stdin=tc["stdin"],
                    expected_stdout=tc["expected_stdout"],
                    is_hidden=tc["is_hidden"]
                ))
            session.add_all(tc_list)
            await session.commit()
            public_cnt = sum(1 for tc in q_data["test_cases"] if not tc["is_hidden"])
            hidden_cnt = sum(1 for tc in q_data["test_cases"] if tc["is_hidden"])
            print(f"    ✓ Added {public_cnt} visible and {hidden_cnt} hidden test cases.")

    print("✅ Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())
