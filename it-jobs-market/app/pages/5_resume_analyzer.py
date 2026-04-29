from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.cards import job_card, page_header, render_metric_cards
from app.components.charts import apply_figure_style, gauge_chart
from app.components.llm_client import ClaudeRecommendationClient
from app.data.loader import find_matching_vacancies, get_top_skills_for_role, summarize_resume_text


def _resume_improvement_notes(missing_skills: list[str], matched_skills: list[str], percentile: float) -> list[str]:
    notes = []
    if missing_skills:
        notes.append(f"Add explicit evidence for these market-critical skills: {', '.join(missing_skills[:8])}.")
    if matched_skills:
        notes.append(f"Prominently surface matched skills near the top of the resume: {', '.join(matched_skills[:8])}.")
    if percentile < 50:
        notes.append("The current profile sits below the median market-fit threshold for this target. Strengthen both core tools and delivery outcomes.")
    notes.append("Convert generic responsibility bullets into quantified impact statements with tools, scale, and business results.")
    return notes


def render(bundle: dict[str, object]) -> None:
    df_skills = bundle["skills"]
    df_base = bundle["base"]
    df_salary = bundle["salary"]
    known_skills = bundle["known_skills"]
    llm_client = ClaudeRecommendationClient()

    page_header(
        "🤖 Resume Analyzer",
        "Paste resume text to estimate target-role fit, identify skill gaps, and surface matching vacancies. PDF/DOCX and Claude flows are intentionally stubbed for now.",
    )

    left, right = st.columns((0.42, 0.58))
    with left:
        uploaded_file = st.file_uploader("Upload resume (PDF/DOC/DOCX)", type=["pdf", "doc", "docx"])
        if uploaded_file is not None:
            st.markdown(
                '<div class="stub-box">PDF/DOCX parsing skeleton is prepared, full parser will be implemented later. '
                "For now, please paste resume text below to run the analysis.</div>",
                unsafe_allow_html=True,
            )

        resume_text = st.text_area(
            "Paste resume text",
            height=260,
            placeholder="Paste your resume here. Skills, tools, projects, achievements, and experience all help the matcher.",
        )
        target_category = st.selectbox(
            "Target category",
            options=sorted(df_skills["category_filled"].replace("", pd.NA).dropna().unique().tolist()),
        )
        target_city = st.selectbox(
            "Target city",
            options=sorted(df_base["city_norm"].replace("", pd.NA).dropna().unique().tolist()),
        )
        target_level = st.selectbox(
            "Target level",
            options=sorted(df_skills["level_filled"].astype(str).replace("nan", pd.NA).dropna().unique().tolist()),
        )
        analyze = st.button("🔍 Analyze resume", use_container_width=True)

    if not analyze:
        with right:
            st.info("Run the analyzer to see gap score, recommendations, matching vacancies, and resume improvement notes.")
        return

    if not resume_text.strip():
        st.warning("Paste resume text to run the analysis. File upload exists only as a safe skeleton for now.")
        return

    resume_profile = summarize_resume_text(resume_text, known_skills)
    resume_skills = resume_profile["hard_skills"]
    target_skills = get_top_skills_for_role(df_skills, target_category, target_level, top_n=20)
    resume_set = {skill.casefold(): skill for skill in resume_skills}
    target_set = {skill.casefold(): skill for skill in target_skills}
    matched_skills = sorted(target_set[key] for key in set(resume_set) & set(target_set))
    missing_skills = sorted(target_set[key] for key in set(target_set) - set(resume_set))
    extra_skills = sorted(resume_set[key] for key in set(resume_set) - set(target_set))
    gap_score = round((len(matched_skills) / len(target_skills) * 100), 1) if target_skills else 0.0

    matches = find_matching_vacancies(
        df_base,
        resume_skills,
        category=target_category,
        level=target_level,
        city=target_city,
        top_n=8,
    )
    match_percentile = round(matches["match_score"].mean() * 100, 1) if not matches.empty else 0.0
    target_salary = (
        df_salary[
            (df_salary["category_filled"] == target_category)
            & (df_salary["level_filled"].astype(str) == target_level)
            & (df_salary["city_norm"] == target_city)
        ]["salary_avg_clean"].median()
    )

    with right:
        gauge_col, metric_col = st.columns((0.52, 0.48))
        with gauge_col:
            st.plotly_chart(gauge_chart(gap_score, title="Gap Score"), use_container_width=True)
        with metric_col:
            render_metric_cards(
                [
                    {"icon": "🧠", "label": "Extracted skills", "value": f"{len(resume_skills)}", "delta": "Matched from market vocabulary", "color": "accent_blue"},
                    {"icon": "📈", "label": "Market-fit percentile", "value": f"{match_percentile:.1f}", "delta": "Average job match score × 100", "color": "accent_green"},
                    {"icon": "⏳", "label": "Experience", "value": f"{resume_profile['years_experience']} years" if resume_profile['years_experience'] else "Not found", "delta": resume_profile["current_level"], "color": "accent_violet"},
                    {"icon": "💸", "label": "Target median salary", "value": f"{target_salary:,.0f} ₸" if pd.notna(target_salary) else "Not enough data", "delta": f"{target_city} • {target_level}", "color": "accent_orange"},
                ]
            )

    tabs = st.tabs(["📊 Skill Analysis", "💡 Recommendations", "💼 Matching Vacancies", "📝 Resume Improvement"])

    with tabs[0]:
        chart_data = pd.DataFrame(
            {
                "skill": matched_skills[:12] + missing_skills[:12] + extra_skills[:12],
                "group": (["Matched"] * min(len(matched_skills), 12))
                + (["Missing"] * min(len(missing_skills), 12))
                + (["Extra"] * min(len(extra_skills), 12)),
            }
        )
        if chart_data.empty:
            st.info("No skill overlap could be established from the current resume text.")
        else:
            chart_data["count"] = 1
            fig = px.bar(
                chart_data,
                x="count",
                y="skill",
                color="group",
                orientation="h",
                barmode="group",
                color_discrete_map={"Matched": "#10B981", "Missing": "#EF4444", "Extra": "#6B7280"},
            )
            st.plotly_chart(apply_figure_style(fig, title="Resume skill alignment"), use_container_width=True)
        st.write("Matched skills:", ", ".join(matched_skills[:20]) or "None")
        st.write("Missing skills:", ", ".join(missing_skills[:20]) or "None")
        st.write("Extra skills:", ", ".join(extra_skills[:20]) or "None")

    with tabs[1]:
        role_slice = df_skills[
            (df_skills["category_filled"] == target_category)
            & (df_skills["level_filled"].astype(str) == target_level)
        ]
        missing_skill_stats = []
        for skill in missing_skills[:12]:
            skill_rows = role_slice[role_slice["skills_all_clean_list"].apply(lambda items: skill in items)]
            missing_skill_stats.append(
                {
                    "skill": skill,
                    "demand": int(skill_rows["id"].nunique()),
                    "median_salary": float(skill_rows["salary_avg_analytics"].median()) if not skill_rows.empty else None,
                }
            )
        missing_skill_frame = pd.DataFrame(missing_skill_stats).sort_values(["demand", "median_salary"], ascending=[False, False])
        st.markdown(
            '<div class="stub-box">Claude recommendation tab is prepared as a safe interface. '
            "Live API calls are intentionally disabled in this MVP.</div>",
            unsafe_allow_html=True,
        )
        response = llm_client.get_resume_recommendations(
            {
                "target_category": target_category,
                "target_level": target_level,
                "missing_skills": missing_skills,
                "gap_score": gap_score,
            }
        )
        st.write(response.text)
        if not missing_skill_frame.empty:
            st.dataframe(
                missing_skill_frame.rename(
                    columns={"skill": "skill", "demand": "market_demand", "median_salary": "median_salary_kzt"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tabs[2]:
        if matches.empty:
            st.info("No matching vacancies were found for the current target filters and extracted skills.")
        else:
            for _, row in matches.iterrows():
                job_card(
                    title=row["title_display"],
                    company=row["company_display"],
                    salary=row["salary_display"],
                    meta=f"{row['city_norm'] or 'city n/a'} • {row['work_format_norm'] or 'format n/a'} • {row['category_display']}",
                    match_score=float(row["match_score"]),
                    skills=row["matched_skills"],
                    url=row["source_url"],
                )
                st.caption(
                    "Why this job matches: "
                    + (", ".join(row["matched_skills"][:8]) if row["matched_skills"] else "limited skill overlap detected")
                )

    with tabs[3]:
        notes = _resume_improvement_notes(missing_skills, matched_skills, match_percentile)
        for note in notes:
            st.write(f"- {note}")
        st.write(
            "- Keep the text-input workflow as the primary path for now; the upload parser and live Claude layer are intentionally left as skeletons."
        )
