import re
import uuid
from pydantic import BaseModel
from app.models.question import Question

# Common prompt injection / adversarial evasion patterns
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|above) instructions",
    r"system override",
    r"unlock (the )?(code )?editor",
    r"give me the (solution|code|answer)",
    r"act as (a )?dan",
    r"jailbreak",
    r"forget (your )?rules",
    r"pretend to be",
    r"you are now (unrestricted|free)",
    r"bypass (the )?limit",
]

class CoachingResult(BaseModel):
    is_approved: bool
    feedback: str
    detected_data_structure: str | None = None
    detected_algorithm: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    missing_requirements: list[str] = []
    starter_code: str | None = None
    tokens_consumed: int = 150

class AICoachService:
    """
    Intelligent DSA Coaching & Guardrail Engine.
    Verifies algorithmic approach, data structure, time/space complexity,
    and defends against prompt injections before unlocking the Monaco editor.
    """

    @staticmethod
    def check_prompt_injection(prompt: str) -> bool:
        """Returns True if adversarial prompt injection is detected."""
        lower_prompt = prompt.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower_prompt):
                return True
        return False

    @classmethod
    def evaluate_approach(
        cls,
        question: Question,
        prompt: str,
        language: str = "python"
    ) -> CoachingResult:
        """
        Evaluates student approach against question requirements.
        """
        # 1. Guardrail: Prompt Injection Defense
        if cls.check_prompt_injection(prompt):
            return CoachingResult(
                is_approved=False,
                feedback="⚠️ **Security Alert:** Prompt injection attempt detected. You must explain your legitimate algorithmic approach and time/space complexity to unlock the editor.",
                missing_requirements=["Legitimate algorithmic explanation"],
                tokens_consumed=80,
            )

        lower = prompt.lower()
        slug = question.slug
        missing = []

        # 2. Extract Complexity mentions (Big-O notation)
        tc_match = re.search(r"o\([n1klog\s\^\*2\+\-]+\)", lower)
        time_complexity = tc_match.group(0).upper() if tc_match else None
        if not time_complexity:
            missing.append("Time Complexity (e.g. O(N), O(N log N))")

        # Check for space complexity mention
        has_space = "space" in lower or "o(1)" in lower or "o(n)" in lower
        if not has_space:
            missing.append("Space Complexity (e.g. O(1), O(N))")

        # 3. Problem-Specific Algorithmic Soundness Check
        detected_ds = None
        detected_algo = None
        is_sound = False
        specific_feedback = ""

        if slug == "two-sum":
            if "hash" in lower or "map" in lower or "dict" in lower:
                detected_ds = "Hash Map / Dictionary"
                detected_algo = "One-Pass Hash Map"
                is_sound = True
                specific_feedback = "Excellent! Using a Hash Map allows complement lookups in O(1) average time, achieving the optimal O(N) overall runtime."
            elif "nested" in lower or "brute" in lower or "o(n^2)" in lower or "o(n*n)" in lower or "two loops" in lower:
                detected_ds = "Array"
                detected_algo = "Brute Force"
                is_sound = False
                specific_feedback = "Your brute-force approach works, but with N up to 10^4 elements, an O(N^2) solution will likely trigger a **Time Limit Exceeded (TLE)**. How can you use an auxiliary data structure to look up complements in O(1) time?"
            elif "two pointer" in lower or "sort" in lower:
                detected_ds = "Sorted Array"
                detected_algo = "Sorting + Two Pointers"
                is_sound = True
                specific_feedback = "Good intuition! Sorting and two pointers yields O(N log N) time. However, remember the problem asks for the **original indices**, so you will need to track elements with their original index before sorting."
            else:
                missing.append("Appropriate Data Structure (e.g. Hash Map)")
                specific_feedback = "Please specify which data structure you plan to use to store and search for numbers."

        elif slug == "valid-parentheses":
            if "stack" in lower:
                detected_ds = "Stack (LIFO)"
                detected_algo = "Parenthesis Matching"
                is_sound = True
                specific_feedback = "Spot on! A Stack is the optimal data structure because the last opened bracket must be the first one closed."
            elif "counter" in lower or "count" in lower or "integer" in lower:
                detected_ds = "Counters"
                detected_algo = "Counting"
                is_sound = False
                specific_feedback = "Be careful: counting the number of open and closed brackets fails for mismatched bracket orders like `([)]`. You need a structure that preserves the order of brackets."
            else:
                missing.append("Appropriate Data Structure (e.g. Stack)")
                specific_feedback = "Consider a data structure that processes the most recently opened bracket first."

        elif slug == "reverse-linked-list":
            if "pointer" in lower or "prev" in lower or "iterat" in lower or "recurs" in lower:
                detected_ds = "Singly Linked List"
                detected_algo = "Three Pointers / Recursive Pointer Reversal"
                is_sound = True
                specific_feedback = "Great! Tracking previous, current, and next pointers allows you to reverse links in-place with O(N) time and O(1) extra space."
            else:
                missing.append("Pointer Manipulation Strategy (e.g. Iterative with prev/curr pointers)")
                specific_feedback = "Explain how you will rewire the `next` pointers of each node without losing reference to the remainder of the list."

        else:
            # Generic fallback
            is_sound = len(prompt.split()) >= 10

        # 4. Final Approval Evaluation
        is_approved = is_sound and (len(missing) == 0)

        # Retrieve language-specific starter code if approved
        starter_code = None
        if is_approved:
            starter_code = question.starter_code.get(language) or question.starter_code.get("python")

        # Build full feedback
        if is_approved:
            full_feedback = f"🎉 **Approach Approved!**\n\n{specific_feedback}\n\n**Algorithm:** {detected_algo}\n**Data Structure:** {detected_ds}\n\nThe code editor has been **unlocked**. Your starter code has been loaded into Monaco."
        else:
            reasons = "\n".join([f"- {m}" for m in missing]) if missing else ""
            full_feedback = f"💡 **Coach Feedback:**\n\n{specific_feedback}\n\n"
            if missing:
                full_feedback += f"**To unlock the code editor, please also address:**\n{reasons}"

        # Estimate realistic token consumption
        tokens_consumed = min(int(len(prompt.split()) * 1.5 + len(full_feedback.split()) * 1.3), 350)

        return CoachingResult(
            is_approved=is_approved,
            feedback=full_feedback,
            detected_data_structure=detected_ds,
            detected_algorithm=detected_algo,
            time_complexity=time_complexity,
            space_complexity="O(1)" if "o(1)" in lower else ("O(N)" if "o(n)" in lower else None),
            missing_requirements=missing,
            starter_code=starter_code,
            tokens_consumed=tokens_consumed,
        )
