from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from app.components.cards import job_card, page_header, render_metric_cards
from app.data.loader import find_matching_vacancies, summarize_resume_text


def _fallback_token_skills(text: str) -> list[str]:
    tokens = [token.strip() for token in re.split(r"[\n,;/]+", text) if token.strip()]
    return tokens[:20]


def render(bundle: dict[str, object]) -> None:
    df_base = bundle["base"]
    known_skills = bundle["known_skills"]

    page_header(
        "🔍 Job Matcher",
        "Paste your skills or resume text, then narrow by city, level, category, work format, and salary to surface the best-fit vacancies from the real dataset.",
    )

    input_col, result_col = st.columns((0.4, 0.6))
    with input_col:
        profile_text = st.text_area(
            "Describe your skills and experience",
            height=220,
            placeholder="Python, SQL, dbt, Airflow, analytics, stakeholder communication...",
        )
        category = st.selectbox(
            "Category",
            options=[""] + sorted(df_base["category_filled"].replace("", pd.NA).dropna().unique().tolist()),
            format_func=lambda value: value or "Any category",
        )
        city = st.selectbox(
            "City",
            options=[""] + sorted(df_base["city_norm"].replace("", pd.NA).dropna().unique().tolist()),
            format_func=lambda value: value or "Any city",
        )
        level = st.selectbox(
            "Level",
            options=[""] + sorted(df_base["level_filled"].astype(str).replace("nan", pd.NA).dropna().unique().tolist()),
            format_func=lambda value: value or "Any level",
        )
        work_format = st.selectbox(
            "Work format",
            options=[""] + sorted(df_base["work_format_norm"].astype(str).replace("nan", pd.NA).dropna().unique().tolist()),
            format_func=lambda value: value or "Any work format",
        )
        salary_values = df_base["salary_avg_clean"].dropna()
        salary_min = 0
        if not salary_values.empty:
            salary_min = st.slider(
                "Minimum salary",
                min_value=0,
                max_value=int((salary_values.max() // 50_000 + 1) * 50_000),
                value=0,
                step=50_000,
            )
        find_jobs = st.button("🔍 Find matching jobs", use_container_width=True)

    if not find_jobs:
        with result_col:
            st.info("Run the matcher to see the top 5 to 10 matching vacancies and rule-based explanations.")
        return

    if not profile_text.strip():
        st.warning("Paste some skills or resume text first.")
        return

    profile = summarize_resume_text(profile_text, known_skills)
    candidate_skills = profile["hard_skills"] or _fallback_token_skills(profile_text)
    matches = find_matching_vacancies(
        df_base,
        candidate_skills,
        category=category,
        level=level,
        city=city,
        work_format=work_format,
        salary_min=salary_min if salary_min > 0 else None,
        top_n=10,
    )

    with result_col:
        render_metric_cards(
            [
                {"icon": "🧠", "label": "Detected skills", "value": f"{len(candidate_skills)}", "delta": "Used for matching", "color": "accent_blue"},
                {"icon": "📌", "label": "Matching jobs", "value": f"{len(matches)}", "delta": "Top results after filters", "color": "accent_green"},
                {"icon": "🎯", "label": "Best match", "value": f"{matches['match_score'].max() * 100:.1f}%" if not matches.empty else "0%", "delta": "Jaccard similarity", "color": "accent_violet"},
                {"icon": "💸", "label": "Top salary", "value": f"{matches['salary_avg_clean'].max():,.0f} ₸" if not matches.empty and matches['salary_avg_clean'].notna().any() else "Not specified", "delta": "Within matched jobs", "color": "accent_orange"},
            ]
        )

        st.write("Detected skills:", ", ".join(candidate_skills[:20]) or "None")
        if matches.empty:
            st.warning("No vacancies matched the current combination of text and filters. Try removing level or city constraints.")
            return

        for _, row in matches.iterrows():
            overlap = row["matched_skills"][:8]
            missing = row["missing_skills_for_job"][:6]
            job_card(
                title=row["title_display"],
                company=row["company_display"],
                salary=row["salary_display"],
                meta=f"{row['city_norm'] or 'city n/a'} • {row['work_format_norm'] or 'format n/a'} • {row['category_display']}",
                match_score=float(row["match_score"]),
                skills=overlap,
                url=row["source_url"],
            )
            with st.expander("Why this job matches"):
                st.write(
                    "Overlap:",
                    ", ".join(overlap) if overlap else "very limited overlap; this role surfaced because the filtered pool is narrow.",
                )
                st.write(
                    "Still missing:",
                    ", ".join(missing) if missing else "no obvious missing skills from the stored vacancy skill list.",
                )

        table = matches[
            [
                "title_display",
                "company_display",
                "city_norm",
                "work_format_norm",
                "salary_display",
                "match_score",
                "source_url",
            ]
        ].rename(
            columns={
                "title_display": "title",
                "company_display": "company",
                "city_norm": "city",
                "work_format_norm": "work_format",
                "salary_display": "salary",
                "match_score": "match_score",
                "source_url": "source_url",
            }
        )
        table["match_score"] = (table["match_score"] * 100).round(1)
        st.subheader("Matched jobs table")
        st.dataframe(table, use_container_width=True, hide_index=True)
