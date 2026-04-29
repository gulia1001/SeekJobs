import json
import os

import requests


class LLMClientError(RuntimeError):
    pass


class LLMClient:
    REPO_SCHEMA = {
        "type": "object",
        "properties": {
            "project_type": {"type": "string"},
            "business_goal": {"type": "string"},
            "stack": {"type": "array", "items": {"type": "string"}},
            "resume_bullets": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "string"},
        },
        "required": [
            "project_type",
            "business_goal",
            "stack",
            "resume_bullets",
            "confidence",
        ],
    }

    PROFILE_SCHEMA = {
        "type": "object",
        "properties": {
            "headline": {"type": "string"},
            "summary": {"type": "string"},
            "resume_bullets": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["headline", "summary", "resume_bullets"],
    }

    def __init__(self, provider, api_key, model=None, timeout=45):
        self.provider = provider.lower()
        self.api_key = api_key
        self.timeout = timeout
        if self.provider == "gemini":
            self.model = model or "gemini-2.5-flash-lite"
        elif self.provider == "groq":
            self.model = model or "meta-llama/llama-4-scout-17b-16e-instruct"
        else:
            raise ValueError("provider must be 'gemini' or 'groq'")

    @classmethod
    def from_env(cls, provider=None, model=None):
        provider = (provider or os.getenv("LLM_PROVIDER", "groq")).strip().lower()
        if not provider:
            return None

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
        else:
            raise ValueError("LLM_PROVIDER must be gemini or groq")

        if not api_key:
            raise LLMClientError(f"{provider.upper()} API key is missing in environment")
        return cls(provider=provider, api_key=api_key, model=model or os.getenv("LLM_MODEL"))

    def enrich_repo(self, repo_payload):
        prompt = self._build_repo_prompt(repo_payload)
        if self.provider == "gemini":
            return self._call_gemini(prompt, self.REPO_SCHEMA)
        return self._call_groq(prompt)

    def build_profile_resume(self, profile_payload):
        prompt = self._build_profile_prompt(profile_payload)
        if self.provider == "gemini":
            return self._call_gemini(prompt, self.PROFILE_SCHEMA)
        return self._call_groq(prompt)

    def _call_gemini(self, prompt, schema):
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
            },
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMClientError(f"Unexpected Gemini response: {data}") from exc

    def _call_groq(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return valid JSON only. Use only the supplied repository evidence. "
                        "If evidence is weak, say so briefly instead of inventing details."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            return json.loads(_strip_json_fence(content))
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMClientError(f"Unexpected Groq response: {data}") from exc

    @staticmethod
    def _build_repo_prompt(repo_payload):
        compact = json.dumps(repo_payload, ensure_ascii=False, indent=2)
        return (
            "You are turning GitHub repository evidence into resume-ready output.\n"
            "Infer only from the provided evidence.\n"
            "Return JSON with keys: project_type, business_goal, stack, resume_bullets, confidence.\n"
            "Rules:\n"
            "- resume_bullets must contain exactly 2 short bullets.\n"
            "- Each bullet must sound like a CV line starting with a strong verb.\n"
            "- Keep stack to at most 6 items.\n"
            "- If business purpose is unclear, say 'Public repository with unclear end-user goal'.\n\n"
            f"Repository evidence:\n{compact}"
        )

    @staticmethod
    def _build_profile_prompt(profile_payload):
        compact = json.dumps(profile_payload, ensure_ascii=False, indent=2)
        return (
            "You are synthesizing a GitHub profile into a concise resume summary.\n"
            "Return JSON with keys: headline, summary, resume_bullets.\n"
            "Rules:\n"
            "- headline: 6-12 words.\n"
            "- summary: 2 sentences max.\n"
            "- resume_bullets: exactly 4 bullets.\n"
            "- Use only the supplied evidence and avoid hype.\n\n"
            f"Profile evidence:\n{compact}"
        )


def _strip_json_fence(content):
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
