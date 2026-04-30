"""Analyse a GitHub profile using the existing scraper."""
import os
import sys

SCRAPER_PATH = os.path.join(
    os.path.dirname(__file__), "../../airflow/GitHub-Profile-Scraper-master"
)
sys.path.insert(0, os.path.abspath(SCRAPER_PATH))


def analyze_github(github_url: str) -> dict:
    """Return a summary dict with skills and repo info, or {} on failure."""
    try:
        username = _extract_username(github_url)
        if not username:
            return {}

        token = os.getenv("GITHUB_TOKEN")
        from github_api import GitHubClient  # type: ignore
        from profile_analyzer import analyze_profile  # type: ignore

        client = GitHubClient(token=token)
        profile = analyze_profile(client, username, output_dir="/tmp/gh_analysis", max_repos=8, llm_client=None)

        skills: list[str] = []
        for repo in profile.get("repos", []):
            skills.extend(repo.get("stack_signals", []))
        skills = _dedupe(skills)

        top_repos = [
            {
                "name": r["name"],
                "description": r.get("business_goal", ""),
                "stack": r.get("stack_signals", []),
                "stars": r.get("stargazers_count", 0),
                "url": r.get("html_url", ""),
            }
            for r in profile.get("repos", [])[:5]
        ]

        return {
            "username": username,
            "bio": profile.get("bio") or "",
            "skills": skills,
            "top_repos": top_repos,
            "summary": f"GitHub: {username} — {len(profile.get('repos', []))} repos, top stack: {', '.join(skills[:5])}",
        }
    except Exception as e:
        return {"error": str(e)}


def _extract_username(url: str) -> str:
    url = url.strip().rstrip("/")
    # plain username with no slashes → use as-is
    if "/" not in url:
        return url
    parts = url.split("/")
    for i, p in enumerate(parts):
        if "github.com" in p and i + 1 < len(parts):
            return parts[i + 1]
    return parts[-1] if parts else ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
