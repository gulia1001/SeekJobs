# GitHub Profile Resume Analyzer

This project now has two layers:

1. Legacy demo scripts: `user.py`, `repo.py`, `commit.py`
2. New production flow for your real goal: analyze a public GitHub profile by `username`, extract project evidence, and generate resume-ready descriptions with minimal LLM cost

## What It Collects

For each public repository, the new flow can collect:

- repository metadata: `description`, `topics`, `language`, `stargazers_count`, `forks_count`, `updated_at`, homepage
- README text
- language breakdown
- root-level stack signals such as `package.json`, `requirements.txt`, `Dockerfile`, `pom.xml`, `Cargo.toml`, `go.mod`, `tailwind.config.*`
- lightweight commit activity sample for the target username
- optional pinned repos when `GITHUB_TOKEN` is available

## What It Produces

The analyzer creates:

- a structured JSON profile analysis
- a Markdown file with resume-oriented summaries
- optional LLM-enriched CV bullets using cheap Groq or Gemini models

## Architecture

### 1. GitHub collection layer

File: `github_api.py`

Responsibilities:

- call GitHub REST API
- paginate repositories
- fetch README
- fetch languages
- fetch root files
- sample commits
- fetch pinned repos through GraphQL when a GitHub token is available

### 2. Heuristic analysis layer

File: `profile_analyzer.py`

Responsibilities:

- detect stack from languages, file names, dependency files, and README hints
- classify repository type such as `api`, `frontend`, `scraper`, `bot`, `ml`, `automation`
- infer business goal from `description` and README intro
- estimate visible activity from sampled commits
- rank repositories by resume relevance
- build fallback resume bullets even without LLM

### 3. Cheap LLM enrichment layer

File: `llm_client.py`

Responsibilities:

- optionally enrich top repositories with short CV bullets
- optionally synthesize a profile-level resume summary
- keep prompts small by sending only compact evidence, not the full raw repository payload

Supported providers:

- `groq` via Groq Chat Completions API
- `gemini` via Gemini Developer API

Recommended models:

- Groq default: `meta-llama/llama-4-scout-17b-16e-instruct`
- Groq fallback for higher daily request volume: `llama-3.1-8b-instant`
- Gemini fallback: `gemini-2.5-flash-lite`

## Why This Is Cheap

To minimize API usage:

- the script first does deterministic analysis without any LLM
- only top repositories are sent to the model
- only compact evidence is sent: description, topics, stack signals, readme excerpt, activity summary
- the prompt asks for strict short JSON, which reduces output tokens

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Configuration

The project reads settings from a local `.env` file automatically.

Created files:

- `.env` for your real keys
- `.env.example` as a template

Default `.env` values:

```bash
LLM_PROVIDER=groq
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
GROQ_API_KEY=
GITHUB_TOKEN=
OUTPUT_DIR=analysis_output
MAX_REPOS=12
MAX_COMMIT_PAGES=2
LLM_TOP_N=3
INCLUDE_FORKS=false
SKIP_LLM=false
```

Notes:

- `GROQ_API_KEY` is used for CV rewriting
- `GITHUB_TOKEN` is strongly recommended for higher GitHub limits and pinned repositories

## Usage

Basic run without LLM:

```bash
python3 analyze_profile.py torvalds --skip-llm
```

Run with `.env` only:

```bash
python3 analyze_profile.py
```

Then the script asks for the username:

```text
Enter GitHub username:
```

Run with Groq:

```bash
python3 analyze_profile.py torvalds
```

Useful flags:

```bash
python3 analyze_profile.py torvalds \
  --max-repos 15 \
  --max-commit-pages 2 \
  --llm-top-n 5 \
  --output-dir analysis_output
```

## Output Files

After a run you will get:

- `analysis_output/<username>_analysis.json`
- `analysis_output/<username>_resume.md`

## Notes About Accuracy

This tool is strongest at:

- public project discovery
- stack inference
- turning repository evidence into concise resume language

This tool is weaker when:

- README is missing or low quality
- the repository hides the real business goal
- the profile contains many tiny experiments instead of a few flagship projects

For best results:

- use a `GITHUB_TOKEN`
- keep `llm_top_n` low
- prefer Groq only for rewriting, not for raw repo exploration

## Why This Groq Model

Default choice: `meta-llama/llama-4-scout-17b-16e-instruct`

Why it fits this project better than the other options you listed:

- noticeably stronger than `llama-3.1-8b-instant` for short professional rewrites
- still has a generous `30K TPM` and `500K tokens/day`
- `1K requests/day` is enough because this tool only calls the model for the top few repositories plus one profile summary
- `compound` models are unnecessary here because we do not need tool orchestration
- `70b` and `120b` options are overkill for this narrow JSON task and have tighter daily token budgets

## Legacy Files

The original `user.py`, `repo.py`, and `commit.py` are still present as lightweight GitHub API examples, but the main workflow is now `analyze_profile.py`.
