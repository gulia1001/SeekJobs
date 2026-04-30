"""Parse LinkedIn profile via the existing Node.js Apify service or direct Apify SDK."""
import os
import httpx


async def parse_linkedin(linkedin_url: str) -> dict:
    """Try the Node.js service first, fall back to Apify SDK, return {} on all failures."""
    result = await _try_nodejs_service(linkedin_url)
    if result:
        return result
    result = _try_apify_sdk(linkedin_url)
    return result or {}


async def _try_nodejs_service(url: str) -> dict:
    """POST to the Node.js express server that wraps Apify."""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(
                "http://localhost:3000/api/parse",
                json={"url": url},
                headers={"Content-Type": "application/json"},
            )
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return {}


def _try_apify_sdk(url: str) -> dict:
    """Direct Apify call — requires APIFY_TOKEN env var."""
    token = os.getenv("APIFY_TOKEN")
    if not token:
        return {}
    try:
        from apify_client import ApifyClient  # type: ignore

        client = ApifyClient(token)
        run = client.actor("harvestapi/linkedin-profile-scraper").call(
            run_input={"urls": [url], "proxyConfiguration": {"useApifyProxy": True}}
        )
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        if not items:
            return {}
        raw = items[0]
        return _clean(raw)
    except Exception as e:
        return {"error": str(e)}


def _clean(raw: dict) -> dict:
    raw_certs = raw.get("certifications") or raw.get("licensesAndCertifications") or []
    return {
        "fullName": f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip() or raw.get("name", ""),
        "headline": raw.get("headline", ""),
        "location": (raw.get("location") or {}).get("parsed", {}).get("text", ""),
        "experience": [
            {
                "title": e.get("position") or e.get("title", ""),
                "company": e.get("companyName", ""),
                "start": (e.get("startDate") or {}).get("text", "N/A"),
                "end": (e.get("endDate") or {}).get("text", "Present"),
            }
            for e in (raw.get("experience") or [])
        ],
        "education": [
            {
                "school": edu.get("schoolName") or edu.get("school", ""),
                "degree": edu.get("degree", ""),
                "period": edu.get("period", ""),
            }
            for edu in (raw.get("education") or [])
        ],
        "certifications": [
            {
                "name": c.get("name") or c.get("title", ""),
                "authority": c.get("authority") or c.get("issuingOrganizationName", ""),
            }
            for c in raw_certs
        ],
        "skills": [
            (s if isinstance(s, str) else s.get("name", ""))
            for s in (raw.get("skills") or [])
        ],
    }
