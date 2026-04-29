import argparse
import json
import os

from env_loader import env_bool, env_int, load_env_file
from github_api import GitHubClient
from llm_client import LLMClient
from profile_analyzer import analyze_profile


def parse_args():
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Analyze a public GitHub profile and draft resume-ready project summaries."
    )
    parser.add_argument("username", nargs="?", help="GitHub username to analyze")
    parser.add_argument(
        "--output-dir",
        default=os.getenv("OUTPUT_DIR", "analysis_output"),
        help="Where to store JSON and Markdown outputs",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=env_int("MAX_REPOS", 12),
        help="Maximum number of repositories to analyze",
    )
    parser.add_argument(
        "--max-commit-pages",
        type=int,
        default=env_int("MAX_COMMIT_PAGES", 2),
        help="How many 100-commit pages to sample per repo",
    )
    parser.add_argument(
        "--include-forks",
        action="store_true",
        default=env_bool("INCLUDE_FORKS", False),
        help="Include forked repositories",
    )
    parser.add_argument("--provider", choices=["gemini", "groq"], help="Optional LLM provider override")
    parser.add_argument("--model", help="Optional LLM model override")
    parser.add_argument(
        "--llm-top-n",
        type=int,
        default=env_int("LLM_TOP_N", 3),
        help="Run LLM enrichment only for the top N repositories",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        default=env_bool("SKIP_LLM", False),
        help="Disable Gemini/Groq even if API keys are present",
    )
    return parser.parse_args()


def resolve_username(cli_username):
    if cli_username:
        return cli_username.strip()

    entered = input("Enter GitHub username: ").strip()
    if entered:
        return entered

    raise SystemExit("GitHub username is required.")


def main():
    args = parse_args()
    username = resolve_username(args.username)

    client = GitHubClient()
    llm_client = None if args.skip_llm else LLMClient.from_env(provider=args.provider, model=args.model)

    summary = analyze_profile(
        client=client,
        username=username,
        output_dir=args.output_dir,
        max_repos=args.max_repos,
        max_commit_pages=args.max_commit_pages,
        include_forks=args.include_forks,
        llm_client=llm_client,
        llm_top_n=args.llm_top_n,
    )

    preview = {
        "username": summary["username"],
        "repo_count": len(summary["repos"]),
        "top_repos": [repo["name"] for repo in summary["repos"][:5]],
        "llm_enabled": bool(llm_client),
    }
    print(json.dumps(preview, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
