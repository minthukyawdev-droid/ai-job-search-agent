import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)
jobs = json.loads(Path("data/sample_jobs.json").read_text(encoding="utf-8"))

import_response = client.post("/jobs/import", json={"source": "json", "jobs": jobs, "limit": len(jobs)})
assert import_response.status_code == 200, import_response.text

stats_response = client.get("/jobs/stats")
assert stats_response.status_code == 200, stats_response.text
stats = stats_response.json()
assert stats["total"] == len(jobs), stats

search_response = client.get(
    "/jobs/search",
    params={"query": "entry level backend engineer jobs with AWS and Python in Singapore"},
)
assert search_response.status_code == 200, search_response.text
filters = search_response.json()["filters"]
assert filters == {
    "role": "Backend Engineer",
    "seniority": "entry",
    "location": "Singapore",
    "skills": ["AWS", "Python"],
    "remote": None,
}, filters

print("Backend smoke test passed.")
