
import pandas as pd
df = pd.read_csv('c:/JobHelp/airflow/it-jobs-market/data/final/analysis_ready_jobs_salary_fixed_v3.csv', nrows=5)
print(df.columns.tolist())
