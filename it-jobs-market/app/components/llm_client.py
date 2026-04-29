from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    text: str
    used_live_api: bool = False
    model: str = "stub"


class ClaudeRecommendationClient:
    """Safe placeholder interface for future Claude integration."""

    def __init__(self, api_key: str | None = None, model: str = "claude_stub") -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or ""
        self.model = model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_resume_recommendations(self, context: dict[str, Any]) -> LLMResponse:
        category = context.get("target_category") or "target role"
        level = context.get("target_level") or "target level"
        missing = context.get("missing_skills") or []
        skills_preview = ", ".join(missing[:5]) if missing else "the missing skills identified in the gap analysis"
        return LLMResponse(
            text=(
                "Claude integration skeleton is ready, but live recommendations are intentionally disabled for now. "
                f"For this profile, the current non-LLM recommendation is to focus on {skills_preview} "
                f"to improve fit for {level} {category} roles."
            )
        )

    def explain_job_match(self, context: dict[str, Any]) -> LLMResponse:
        overlap = context.get("matched_skills") or []
        overlap_text = ", ".join(overlap[:6]) if overlap else "core overlapping skills"
        return LLMResponse(
            text=(
                "Claude explanation skeleton is prepared. "
                f"Current fallback explanation: this role matches mainly because of {overlap_text}."
            )
        )
