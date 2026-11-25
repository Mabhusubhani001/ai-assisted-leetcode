import { notFound } from "next/navigation";
import { PracticeWorkspace } from "@/components/workspace/PracticeWorkspace";
import { QuestionDetail } from "@/types/problem";

interface ProblemPageProps {
  params: Promise<{
    slug: string;
  }>;
}

// Fallback seed catalog for offline prerendering and fast development SSR
const FALLBACK_QUESTIONS: Record<string, QuestionDetail> = {
  "two-sum": {
    id: "9ab21dc3-87d5-4961-8fdc-158c3dfd2260",
    title: "Two Sum",
    slug: "two-sum",
    difficulty: "Easy",
    description: `# Two Sum

Given an array of integers \`nums\` and an integer \`target\`, return **indices of the two numbers** such that they add up to \`target\`.

You may assume that each input would have **exactly one solution**, and you may not use the same element twice.

### Example 1:
\`\`\`text
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
\`\`\`

### Example 2:
\`\`\`text
Input: nums = [3,2,4], target = 6
Output: [1,2]
\`\`\`

### Constraints:
* \`2 <= nums.length <= 10^4\`
* \`-10^9 <= nums[i] <= 10^9\`
* \`-10^9 <= target <= 10^9\`
* **Only one valid answer exists.**
`,
    starter_code: {
      python: "class Solution:\n    def twoSum(self, nums: list[int], target: int) -> list[int]:\n        pass\n",
      cpp: "#include <vector>\n\nclass Solution {\npublic:\n    std::vector<int> twoSum(std::vector<int>& nums, int target) {\n        \n    }\n};\n",
      java: "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
      javascript: "var twoSum = function(nums, target) {\n    \n};\n",
    },
    memory_limit_mb: 256,
    time_limit_sec: 2.0,
    test_cases: [
      { id: "tc-1", stdin: "2 7 11 15\n9", expected_stdout: "[0, 1]" },
      { id: "tc-2", stdin: "3 2 4\n6", expected_stdout: "[1, 2]" },
      { id: "tc-3", stdin: "3 3\n6", expected_stdout: "[0, 1]" },
    ],
  },
  "valid-parentheses": {
    id: "8c12a860-2641-4770-b196-419b45e9944a",
    title: "Valid Parentheses",
    slug: "valid-parentheses",
    difficulty: "Easy",
    description: `# Valid Parentheses

Given a string \`s\` containing just the characters \`'('\`, \`')'\`, \`'{'\`, \`'}'\`, \`'['\` and \`']'\`, determine if the input string is valid.

### Example 1:
\`\`\`text
Input: s = "()"
Output: true
\`\`\`

### Constraints:
* \`1 <= s.length <= 10^4\`
* \`s\` consists of parentheses only \`'()[]{}'\`.
`,
    starter_code: {
      python: "class Solution:\n    def isValid(self, s: str) -> bool:\n        pass\n",
      cpp: "class Solution {\npublic:\n    bool isValid(std::string s) {\n        \n    }\n};\n",
      java: "class Solution {\n    public boolean isValid(String s) {\n        return false;\n    }\n}\n",
      javascript: "var isValid = function(s) {\n    \n};\n",
    },
    memory_limit_mb: 256,
    time_limit_sec: 2.0,
    test_cases: [
      { id: "tc-1", stdin: "()", expected_stdout: "true" },
      { id: "tc-2", stdin: "()[]{}", expected_stdout: "true" },
      { id: "tc-3", stdin: "(]", expected_stdout: "false" },
    ],
  },
  "reverse-linked-list": {
    id: "3df20336-3914-411a-ab93-4a180fec7aa4",
    title: "Reverse Linked List",
    slug: "reverse-linked-list",
    difficulty: "Easy",
    description: `# Reverse Linked List

Given the head of a singly linked list, reverse the list, and return the reversed list.

### Example 1:
\`\`\`text
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]
\`\`\`
`,
    starter_code: {
      python: "class Solution:\n    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:\n        pass\n",
      cpp: "class Solution {\npublic:\n    ListNode* reverseList(ListNode* head) {\n        \n    }\n};\n",
      java: "class Solution {\n    public ListNode reverseList(ListNode head) {\n        return null;\n    }\n}\n",
      javascript: "var reverseList = function(head) {\n    \n};\n",
    },
    memory_limit_mb: 256,
    time_limit_sec: 2.0,
    test_cases: [
      { id: "tc-1", stdin: "1 2 3 4 5", expected_stdout: "[5, 4, 3, 2, 1]" },
      { id: "tc-2", stdin: "1 2", expected_stdout: "[2, 1]" },
      { id: "tc-3", stdin: "", expected_stdout: "[]" },
    ],
  },
};

async function getProblem(slug: string): Promise<QuestionDetail | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${apiUrl}/api/v1/questions/${slug}`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // If backend is unreachable during build prerendering, use fallback seeds
  }
  return FALLBACK_QUESTIONS[slug] || null;
}

export default async function ProblemPage({ params }: ProblemPageProps) {
  const { slug } = await params;
  const problem = await getProblem(slug);

  if (!problem) {
    notFound();
  }

  return <PracticeWorkspace problem={problem} />;
}
