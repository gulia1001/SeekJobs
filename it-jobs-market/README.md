# IT Jobs Market

Streamlit dashboard and data pipeline for Kazakhstan IT job market analysis across HH, Kaspi, Kolesa, and Telegram sources.

## Run

```bash
streamlit run main.py
```

## Project Structure

```text
IT Jobs Market/
├── app/                     # Streamlit app
├── llm/                     # LLM enrichment pipeline modules
├── data_collection/         # Source collection notebooks
├── telegram-scraper/        # Telegram scraping utility
├── datasets IT Jobs/        # Raw source exports used by the integration pipeline
├── data/
│   ├── final/               # Final curated datasets and marts
│   ├── interim/             # Upstream integrated / enriched datasets
│   └── reports/             # Machine-readable reports and audit artifacts
├── docs/                    # Active documentation
├── trash/                   # Old versions, drafts, exports, and non-active artifacts
├── main.py                  # Root Streamlit entrypoint
├── job_integration_pipeline.py
├── prepare_analysis_ready_jobs.py
└── repair_salary_layer_v2.py
```

## Active Data Flow

1. `datasets IT Jobs/` -> `job_integration_pipeline.py` -> `data/interim/unified_job_database.csv`
2. `llm/` enrichment pipeline -> `data/interim/enriched_jobs_full_v1.csv`
3. `prepare_analysis_ready_jobs.py` -> `data/final/analysis_ready_jobs.csv`
4. `repair_salary_layer_v2.py` -> `data/final/analysis_ready_jobs_salary_fixed_v3.csv`
5. `app/` reads `data/final/analysis_ready_jobs_salary_fixed_v3.csv`

## Main Docs

- `docs/README_ANALYSIS_READY_DATASET_RU_EN.md`
- `docs/README_LLM_INTEGRATION.md`

