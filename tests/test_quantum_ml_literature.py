"""Offline source-connector contracts; live network is never required by CI."""

from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("numpy")

from energy_agents.quantum_ml import run_quantum_ml_agent, synthetic_load_case  # noqa: E402
from energy_agents.quantum_ml.literature import (  # noqa: E402
    fetch_arxiv_literature,
    parse_arxiv_feed,
)

FEED = b'''<feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2601.00001v1</id><title>Quantum forecasting fixture</title>
<published>2026-01-01T00:00:00Z</published><updated>2026-01-02T00:00:00Z</updated>
<author><name>Example Author</name></author><summary>Not copied into the ledger.</summary>
</entry></feed>'''


def test_fixed_https_query_budgets_provenance_and_no_copied_abstract(monkeypatch):
    captured = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, budget):
            assert budget == 1_000_001
            return FEED

    def fake_open(request, timeout):
        captured.append(request.full_url)
        assert timeout == 20
        return Response()

    monkeypatch.setattr("energy_agents.quantum_ml.literature.urlopen", fake_open)
    report = fetch_arxiv_literature(query='all:"quantum learning"', max_results=3)
    parsed = urlparse(captured[0])
    assert (parsed.scheme, parsed.hostname, parsed.path) == ("https", "export.arxiv.org", "/api/query")
    assert parse_qs(parsed.query)["max_results"] == ["3"]
    assert report["live_search_performed_by_agent"] and not report["peer_review_verified"]
    assert len(report["response_sha256"]) == 64 and report["retrieved_at"]
    row = report["entries"][0]
    assert row["url"] == "https://arxiv.org/abs/2601.00001v1"
    assert row["evidence_status"] == "metadata_only_requires_full_text_review"
    assert "summary" not in row


@pytest.mark.parametrize("raw", [b"x" * 1_000_001, b"<!DOCTYPE bad>", b"<html/>",
                                  FEED.replace(b"arxiv.org/abs", b"other.invalid/abs"),
                                  FEED.replace(b"2026-01-01T00:00:00Z", b"bad date")])
def test_malformed_or_unsafe_feeds_fail(raw):
    with pytest.raises(ValueError):
        parse_arxiv_feed(raw)


def test_offline_default_and_explicit_network_stage(monkeypatch):
    calls = []

    def fetch():
        calls.append(True)
        return {"live_search_performed_by_agent": True, "entries": []}

    monkeypatch.setattr("energy_agents.quantum_ml.agent.fetch_arxiv_literature", fetch)
    case = synthetic_load_case(days=12)
    offline = run_quantum_ml_agent(case)
    assert offline["success"] and not calls
    online = run_quantum_ml_agent(case, refresh_literature=True)
    assert online["success"] and len(calls) == 1
    assert len(online["trace"]) == 6
    assert online["reports"]["handoff"]["literature"]["live_search_performed_by_agent"]
