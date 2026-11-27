import asyncio
import json
import logging
import re
from typing import Any
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.models.question import Question

logger = logging.getLogger(__name__)

class LLMCoachingResult(BaseModel):
    is_approved: bool
    feedback: str
    detected_data_structure: str | None = None
    detected_algorithm: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    missing_requirements: list[str] = []
    starter_code: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    turn_tokens: int = 0
    tokens_consumed: int = 0
    provider_used: str = "gemini"
    model_used: str = "gemini-3.8-flash"

SYSTEM_PROMPT_TEMPLATE = """You are a Senior DSA (Data Structures & Algorithms) Mentor and Technical Interview Coach on a disciplined coding assessment platform.

PROBLEM UNDER EVALUATION:
Title: {title}
Description:
{description}

Target Programming Language: {language}

YOUR MISSION & PEDAGOGICAL CONTRACT:
The student's code editor is locked. Your role is to mentor and verify their algorithmic strategy before they write code.
1. NEVER WRITE THE COMPLETE OR WORKING SOLUTION! DO NOT WRITE LOOPS, LOGIC, OR CALCULATIONS FOR THE STUDENT!
2. CONVERSATIONAL MEMORY IS PARAMOUNT: You will be provided with the conversation history between you and the student. If the student already explained part of their strategy (e.g. stated a Hash Map or Stack) in a previous turn, and in the current turn provides the time and space complexity, SYNTHESIZE all turns together! Do NOT ask them to repeat information they already gave you in earlier turns!

APPROVAL CRITERIA (All 4 must be satisfied across the conversation):
1. Problem Understanding: Student shows they understand what needs to be solved.
2. Data Structure: Student selects an optimal data structure (e.g. Hash Map for Two Sum, Stack for Valid Parentheses, Three Pointers for Reverse Linked List).
3. Algorithmic Pattern / Logic: Student explains how they will process inputs (e.g. complement lookup target - nums[i]).
4. Time & Space Complexity: Student states valid Big-O notation (e.g. O(N) time and O(N) space).

STARTER CODE POLICY:
- If is_approved is TRUE:
  Generate ONLY a base starter template in {language} that reflects what the student described in the chat:
  CRITICAL RULES:
  1. Use the standard class and method signature for {language} (e.g. `class Solution:` for Python/Java/C++, or exported function for JavaScript). In Python, if type annotations like `List[int]` are used, include `from typing import List, Optional` at the top.
  2. NEVER WRITE THE COMPLETE OR WORKING SOLUTION! DO NOT WRITE THE LOOPS, CONDITIONS, OR COMPLEMENT CALCULATIONS FOR THE STUDENT!
  3. Include clean, numbered scaffolding comments outlining the specific strategy the student explained in the chat (e.g., `# 1. Initialize hash map to store value -> index`, `# 2. Iterate through nums and check for complement (target - num)`, `# 3. Return matching indices`).
  4. If the student specified a data structure (e.g. Hash Map, Stack), instantiate that empty data structure inside the function (e.g. `seen = {}` for Python, `Map<Integer, Integer> seen = new HashMap<>();` for Java, `unordered_map<int, int> seen;` for C++, `const seen = new Map();` for JavaScript).
  5. DO NOT write the loop or inner logic. Under the comments, insert: `# TODO: Implement logic based on your approach`
  6. Include only the default return statement (e.g. `return []` for Python, `return new int[]{};` for Java, `return {};` for C++).
- If is_approved is FALSE:
  starter_code MUST be null.

OUTPUT FORMAT:
You MUST respond with ONLY a raw JSON object (no markdown code blocks, no trailing conversational text) adhering to this schema:
{{
  "is_approved": boolean,
  "feedback": "Encouraging mentor feedback in Markdown. If approved, praise their strategy and announce starter code is ready. If not approved, specify exactly what is still needed.",
  "detected_data_structure": "string or null",
  "detected_algorithm": "string or null",
  "time_complexity": "string or null",
  "space_complexity": "string or null",
  "missing_requirements": ["list", "of", "missing", "items"],
  "starter_code": "code string or null"
}}
"""

def extract_json_payload(raw_content: str) -> dict[str, Any]:
    """Safely extracts JSON from model response even if wrapped in markdown fences."""
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception:
                pass
        raise ValueError(f"Failed to parse LLM JSON: {cleaned[:200]}")

class LLMCoachService:
    """
    Dedicated Google Gemini Coaching Engine.
    Primary Model: gemini-3.5-flash-lite
    High-Demand Fallback: gemini-3.1-flash-lite
    Strict input-token accounting (the 2,000 budget applies exclusively to input tokens).
    """

    PRIMARY_MODEL = getattr(settings, "GEMINI_PRIMARY_MODEL", None) or "gemini-3.5-flash-lite"
    FALLBACK_MODELS = getattr(settings, "GEMINI_FALLBACK_MODELS", [
        "gemini-3.1-flash-lite",
        "gemini-4-hydrogen",
    ])
    BASE_URL = settings.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/"

    @classmethod
    async def evaluate_with_history(
        cls,
        question: Question,
        current_prompt: str,
        conversation_history: list[dict[str, str]],
        language: str = "python",
        custom_provider: str | None = None,
        custom_api_key: str | None = None,
        custom_model: str | None = None,
    ) -> LLMCoachingResult:
        """
        Sends complete multi-turn conversation to Google Gemini and parses structured evaluation.
        Features automatic failover from gemini-3.5-flash-lite to gemini-3.1-flash-lite on high demand.
        """
        api_key = custom_api_key or settings.GEMINI_API_KEY or ""

        # Graceful fallback if no Gemini API key is provided
        if not api_key:
            from app.services.ai_coach import AICoachService

            # Check injection strictly on current prompt (not past history)
            if AICoachService.check_prompt_injection(current_prompt):
                p_tok = len(current_prompt.split())
                return LLMCoachingResult(
                    is_approved=False,
                    feedback="⚠️ **Security Alert:** Prompt injection attempt detected. You must explain your legitimate algorithmic approach and time/space complexity to unlock the editor.",
                    missing_requirements=["Legitimate algorithmic explanation"],
                    prompt_tokens=p_tok,
                    completion_tokens=30,
                    turn_tokens=p_tok,
                    tokens_consumed=p_tok,
                    provider_used="gemini",
                    model_used="offline_fallback",
                )

            clean_history = [
                m["content"] for m in conversation_history
                if m.get("role") == "user" and not AICoachService.check_prompt_injection(m["content"])
            ]
            full_context = " ".join(clean_history + [current_prompt])

            fallback = AICoachService.evaluate_approach(
                question=question,
                prompt=full_context,
                language=language,
            )
            notice_header = (
                "> **Google Gemini Setup Required:** Please enter your free Google Gemini API key by clicking **⚙️** in the top right to activate live AI coaching.\n\n"
                "> You can generate a free key instantly at [Google AI Studio](https://aistudio.google.com).\n\n"
            )
            return LLMCoachingResult(
                is_approved=fallback.is_approved,
                feedback=notice_header + fallback.feedback,
                detected_data_structure=fallback.detected_data_structure,
                detected_algorithm=fallback.detected_algorithm,
                time_complexity=fallback.time_complexity,
                space_complexity=fallback.space_complexity,
                missing_requirements=fallback.missing_requirements,
                starter_code=fallback.starter_code,
                prompt_tokens=fallback.prompt_tokens,
                completion_tokens=fallback.completion_tokens,
                turn_tokens=fallback.prompt_tokens,
                tokens_consumed=fallback.prompt_tokens,
                provider_used="gemini",
                model_used="offline_fallback",
            )

        client = AsyncOpenAI(base_url=cls.BASE_URL, api_key=api_key, timeout=25.0)

        system_prompt = (
            SYSTEM_PROMPT_TEMPLATE
            .replace("{title}", question.title or "")
            .replace("{description}", question.description or "")
            .replace("{language}", language or "python")
        )

        # Assemble full multi-turn conversation
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for entry in conversation_history:
            messages.append({"role": entry["role"], "content": entry["content"]})
        messages.append({"role": "user", "content": current_prompt})

        # Multi-tier priority waterfall sequence
        if custom_model:
            candidate_models = [custom_model]
        else:
            candidate_models = [cls.PRIMARY_MODEL] + [m for m in cls.FALLBACK_MODELS if m != cls.PRIMARY_MODEL]

        response = None
        last_error = None
        model_used_tag = candidate_models[0]

        try:
            for i, model_candidate in enumerate(candidate_models):
                try:
                    model_used_tag = model_candidate if i == 0 else f"{model_candidate} (fallback)"
                    response = await client.chat.completions.create(
                        model=model_candidate,
                        messages=messages,
                        temperature=0.2,
                        response_format={"type": "json_object"},
                    )
                    break  # Success!
                except Exception as model_err:
                    last_error = model_err
                    err_text = str(model_err).lower()
                    is_high_demand = any(k in err_text for k in ["503", "429", "overloaded", "resource_exhausted", "high demand", "unavailable"])
                    if is_high_demand and i < len(candidate_models) - 1:
                        logger.warning(
                            "Model %s experienced high demand (%s). Failing over to tier %d: %s",
                            model_candidate,
                            model_err,
                            i + 2,
                            candidate_models[i + 1],
                        )
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        raise model_err

            if not response:
                raise last_error or RuntimeError("All candidate Gemini models failed to respond.")

            raw_text = response.choices[0].message.content or "{}"
            parsed = extract_json_payload(raw_text)

            # Extract exact input token count from Gemini response
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else len(current_prompt.split()) * 2
            completion_tokens = usage.completion_tokens if usage else len(raw_text.split()) * 2

            # Determine starter code
            starter_code = parsed.get("starter_code")
            if starter_code:
                fence_match = re.search(r"```(?:\w+)?\s*([\s\S]*?)\s*```", starter_code)
                if fence_match:
                    starter_code = fence_match.group(1).strip()

            is_approved = bool(parsed.get("is_approved", False))
            if is_approved and not starter_code:
                # Fallback to database starter code if model omitted it
                starter_code = question.starter_code.get(language) or question.starter_code.get("python")

            return LLMCoachingResult(
                is_approved=is_approved,
                feedback=parsed.get("feedback", "Approach reviewed."),
                detected_data_structure=parsed.get("detected_data_structure"),
                detected_algorithm=parsed.get("detected_algorithm"),
                time_complexity=parsed.get("time_complexity"),
                space_complexity=parsed.get("space_complexity"),
                missing_requirements=parsed.get("missing_requirements", []),
                starter_code=starter_code,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                turn_tokens=prompt_tokens,  # 2000 budget applies to input tokens
                tokens_consumed=prompt_tokens,
                provider_used="gemini",
                model_used=model_used_tag,
            )

        except Exception as err:
            logger.exception("Gemini Coach invocation error: %s", err)
            err_msg = str(err).lower()

            if "api_key" in err_msg or not client.api_key:
                feedback = (
                    "**Google Gemini API Key Required:**\n\n"
                    "Please enter a valid **Google Gemini API Key** in the settings menu (**⚙️**) above. "
                    "You can get a free key instantly from [Google AI Studio](https://aistudio.google.com)."
                )
                return LLMCoachingResult(
                    is_approved=False,
                    feedback=feedback,
                    missing_requirements=["Active Google Gemini API connection"],
                    prompt_tokens=10,
                    completion_tokens=25,
                    turn_tokens=10,
                    tokens_consumed=10,
                    provider_used="gemini",
                    model_used=model_used_tag,
                )

            # High-resilience fallback: Synthesize full conversation history via deterministic evaluator
            from app.services.ai_coach import AICoachService
            clean_history = [
                m["content"] for m in conversation_history
                if m.get("role") == "user" and not AICoachService.check_prompt_injection(m["content"])
            ]
            full_context = " ".join(clean_history + [current_prompt])
            fallback = AICoachService.evaluate_approach(
                question=question,
                prompt=full_context,
                language=language,
            )
            return LLMCoachingResult(
                is_approved=fallback.is_approved,
                feedback=fallback.feedback,
                detected_data_structure=fallback.detected_data_structure,
                detected_algorithm=fallback.detected_algorithm,
                time_complexity=fallback.time_complexity,
                space_complexity=fallback.space_complexity,
                missing_requirements=fallback.missing_requirements,
                starter_code=fallback.starter_code,
                prompt_tokens=fallback.prompt_tokens,
                completion_tokens=fallback.completion_tokens,
                turn_tokens=fallback.prompt_tokens,
                tokens_consumed=fallback.prompt_tokens,
                provider_used="gemini",
                model_used="resilient_fallback",
            )
