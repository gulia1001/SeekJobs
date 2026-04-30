import os
import requests
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


class GrokClient:
    """Client for Grok (using Groq API as configured in .env)."""

    def __init__(self, api_key: str | None = None, model: str = "llama3-70b-8192") -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or ""
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _call_api(self, prompt: str, system_prompt: str = "You are an expert career coach and technical recruiter.") -> str:
        if not self.is_configured:
            return "Groq API key not found in .env. Please add GROQ_API_KEY."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error calling Groq API: {str(e)}"

    def generate_cv_latex(self, profile: dict[str, Any], top_matches: list[dict[str, Any]]) -> str:
        """Generates a 1-page CV in LaTeX format based on profile and top matching vacancies."""
        matches_text = "\n".join([
            f"- {m['title']} at {m['company']} (Skills: {', '.join(m.get('matched_skills', []))})"
            for m in top_matches
        ])
        
        prompt = f"""
        Generate a professional 1-page CV in standard LaTeX format (using article class, small margins).
        
        Candidate Profile:
        - Skills: {', '.join(profile.get('hard_skills', []))}
        - Experience: {profile.get('years_experience', 'N/A')} years
        - Level: {profile.get('current_level', 'N/A')}
        - LinkedIn: {profile.get('linkedin_url', 'N/A')}
        - GitHub: {profile.get('github_url', 'N/A')}
        - Projects and Certificates: {profile.get('projects_certs', 'N/A')}
        
        The CV should be tailored to these top matching vacancies:
        {matches_text}
        
        Requirements:
        1. Use standard LaTeX packages (geometry, hyperref, enumitem, fontawesome5 if available or just text symbols).
        2. Keep it to exactly 1 page.
        3. Highlight skills that match the target roles.
        4. Include sections for Summary, Experience, Skills, and Projects/Certifications.
        5. If LinkedIn or GitHub are provided, include them in the header.
        
        Return ONLY the LaTeX code starting with \documentclass and ending with \end{{document}}.
        """
        
        return self._call_api(prompt, system_prompt="You are a professional CV writer specialized in LaTeX.")
