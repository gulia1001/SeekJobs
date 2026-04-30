@echo off
echo Starting SeekJobs services...

:: LinkedIn parser (Node.js) — port 3000
start "LinkedIn Parser" cmd /k "cd /d %~dp0airflow\my-linkedin-parser && node index.js"

:: FastAPI backend — port 8000
start "FastAPI Backend" cmd /k "cd /d %~dp0backend && pip install -r requirements.txt -q && uvicorn main:app --reload --port 8001"

:: Next.js frontend — port 3001
start "Next.js Frontend" cmd /k "cd /d %~dp0frontend && npm install && npm run dev"

echo All services launching. Open http://localhost:3001
