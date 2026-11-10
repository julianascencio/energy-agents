"""Explicit opt-in, bounded arXiv metadata retrieval for literature triage."""

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

DEFAULT_QUERY = 'all:"quantum machine learning" AND (all:"time series" OR all:optimization)'
API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 1_000_000


def parse_arxiv_feed(raw: bytes, *, max_results: int = 10) -> list[dict]:
    """Keep source metadata, not unreviewed claims or copied full-text research."""
    if type(max_results) is not int or not 1 <= max_results <= 20:
        raise ValueError("max_results must be in 1..20")
    if len(raw) > MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Oversized feed or forbidden XML declaration")
    root = ElementTree.fromstring(raw)
    if root.tag != ATOM + "feed":
        raise ValueError("Expected an Atom feed")
    result = []
    for entry in root.findall(ATOM + "entry")[:max_results]:
        link = entry.findtext(ATOM + "id", "").strip()
        parsed = urlparse(link)
        if parsed.hostname != "arxiv.org" or not parsed.path.startswith("/abs/"):
            raise ValueError("Unexpected paper identifier (possibly an arXiv API error)")
        title = " ".join(entry.findtext(ATOM + "title", "").split())
        if not title:
            raise ValueError("Missing article title")
        dates = {key: entry.findtext(ATOM + key, "").strip() for key in ("published", "updated")}
        for stamp in dates.values():
            if datetime.fromisoformat(stamp).utcoffset() is None:
                raise ValueError("Article dates need an explicit timezone")
        result.append({"id": parsed.path.removeprefix("/abs/"),
                       "url": "https://arxiv.org" + parsed.path, "title": title,
                       "authors": [" ".join(a.findtext(ATOM + "name", "").split())
                                   for a in entry.findall(ATOM + "author")],
                       **dates, "evidence_status": "metadata_only_requires_full_text_review"})
    return result


def fetch_arxiv_literature(*, query: str = DEFAULT_QUERY, max_results: int = 10) -> dict:
    """Make one 20-second HTTPS request; no credentials, pagination or background task.

    Callers must avoid rapid repeated requests; arXiv asks for at least three
    seconds between requests. This function never retries automatically.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ValueError("query must contain 1..500 characters")
    if type(max_results) is not int or not 1 <= max_results <= 20:
        raise ValueError("max_results must be in 1..20")
    url = API + "?" + urlencode({"search_query": query, "start": 0,
                                "max_results": max_results, "sortBy": "submittedDate",
                                "sortOrder": "descending"})
    request = Request(url, headers={"User-Agent": "energy-agents/0.1 literature-research"})
    with urlopen(request, timeout=20) as response:
        raw = response.read(MAX_BYTES + 1)
    entries = parse_arxiv_feed(raw, max_results=max_results)
    return {"source": API, "query": query, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "response_sha256": hashlib.sha256(raw).hexdigest(), "entries": entries,
            "live_search_performed_by_agent": True, "peer_review_verified": False,
            "scope": "Title/author/date metadata only; query coverage and scientific claims need review."}
