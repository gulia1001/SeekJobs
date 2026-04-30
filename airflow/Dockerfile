FROM apache/airflow:3.0.0

USER airflow

# Install Python packages needed for the ETL pipeline
# pymongo: MongoDB driver
# pandas/numpy: data processing (used by job_integration_pipeline.py)
# groq: optional LLM enrichment via Groq API
RUN pip install --no-cache-dir \
    "pymongo>=4.0.0" \
    "pandas>=2.0.0" \
    "numpy>=1.26.0" \
    "groq>=0.4.0"
