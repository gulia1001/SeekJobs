from __future__ import annotations

import json
from typing import Iterable

from llm.schemas import VacancyLLMInput


SYSTEM_PROMPT = """You are an information extraction engine for job vacancy datasets.

Your task is to extract structured fields from job vacancy text.
Return ONLY valid JSON. Do not explain. Do not add markdown.

Rules:
- Use only information explicitly present in the vacancy text.
- If the field is not clearly stated, return null.
- Do not guess company, city, salary, experience, or English level.
- If parser_hints contains high_confidence labelled values, do not contradict them unless the text clearly proves they are wrong.
- If parser_hints is missing or incomplete, extract missing fields semantically from text.
- Normalize obvious job titles, but do not invent seniority.
- Extract skills as arrays of clean canonical names.
- Separate hard skills, soft skills, and tech stack.
- Do not calculate salary_avg.
- Do not decide duplicate status.
- Do not decide whether vacancy is active.
- Keep requirements and responsibilities short, clean, and useful for analysis.
- Remove emojis, contacts, Telegram links, hashtags, and advertising noise.
- Output must follow the schema exactly.

Category clustering rules:
- Use broad canonical cluster labels, not narrow stack-specific or duplicate variants.
- Prefer one stable cluster for similar roles instead of many near-synonyms.
- Examples:
  - backend, frontend, fullstack, mobile, java engineer, python developer, .net developer -> software_engineering
  - data engineer, data analyst, data scientist, ml engineer, bi analyst -> data
  - qa engineer, test automation, manual qa, sdet -> qa
  - devops, sre, platform engineer, infrastructure engineer, cloud engineer -> devops
  - product manager, product owner -> product
  - project manager, engineering manager, team lead, delivery manager -> management
  - business analyst, system analyst, product analyst -> analytics
  - ui/ux designer, graphic designer, motion designer -> design
- Do not invent overly specific categories when a broad canonical cluster already fits.
- Category names must be lowercase snake_case.

Allowed enums:

category:
["data", "software_engineering", "qa", "devops", "product", "design", "analytics", "security", "management", "support", "marketing", "sales", "hr", "finance", "other", "unknown"]

level:
["intern", "junior", "middle", "senior", "lead", "manager", "unknown"]

employment:
["full_time", "part_time", "contract", "internship", "temporary", "unknown"]

work_format:
["office", "remote", "hybrid", "unknown"]

english_level:
["not_required", "a1", "a2", "b1", "b2", "c1", "c2", "unknown"]

currency:
["KZT", "USD", "EUR", "RUB", "unknown"]"""


def build_batch_prompt(rows: Iterable[VacancyLLMInput]) -> str:
    rows = list(rows)
    payload = {
        "jobs": [row.model_dump(mode="json", exclude_none=True) for row in rows],
    }
    return (
        "Extract structured data for each job and return one JSON object with the exact shape:\n"
        '{"items":[{"id":"...","title_normalized":null,"company":null,"city":null,'
        '"category":"unknown","level":"unknown","employment":"unknown","work_format":"unknown",'
        '"experience_min":null,"experience_max":null,"english_mention":false,"english_required":null,"english_level":"unknown",'
        '"requirements_clean":null,"responsibilities_clean":null,"hard_skills":[],"soft_skills":[],'
        '"tech_stack":[],"salary_raw":null,"salary_from":null,"salary_to":null,"currency":"unknown",'
        '"salary_gross":null,"llm_confidence":0.0}]}\n'
        f"You MUST return exactly {len(rows)} items.\n"
        "Keep the same ids and keep item order aligned with input.\n"
        "Use parser_hints as conservative hints, especially for labelled Telegram values.\n"
        "requirements_clean and responsibilities_clean must be a single string or null, never an array.\n"
        "hard_skills, soft_skills, tech_stack must always be arrays.\n"
        "salary_from and salary_to must be numbers or null.\n"
        "english_mention must be a boolean.\n"
        "english_level must be one of: not_required, a1, a2, b1, b2, c1, c2, unknown.\n"
        "llm_confidence should reflect how much explicit evidence exists in the text, not a guess.\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )
