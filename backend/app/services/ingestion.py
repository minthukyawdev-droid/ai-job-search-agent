import html
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import JobCreate, JobImportRequest


TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class ImportResult:
    jobs: list[JobCreate]


class JobIngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch(self, request: JobImportRequest) -> ImportResult:
        source = request.source.lower()
        if source == "json":
            return ImportResult(jobs=request.jobs or [])
        if source == "remotive":
            return ImportResult(jobs=await self._remotive(request))
        if source == "adzuna":
            return ImportResult(jobs=await self._adzuna(request))
        if source == "greenhouse":
            return ImportResult(jobs=await self._greenhouse(request))
        if source == "lever":
            return ImportResult(jobs=await self._lever(request))
        raise ValueError(f"Unsupported import source: {request.source}")

    async def _remotive(self, request: JobImportRequest) -> list[JobCreate]:
        params: dict[str, Any] = {"limit": request.limit}
        if request.query:
            params["search"] = request.query
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get("https://remotive.com/api/remote-jobs", params=params)
            response.raise_for_status()
        jobs = response.json().get("jobs", [])
        return [
            JobCreate(
                title=item.get("title") or "Untitled role",
                company=item.get("company_name") or "Unknown company",
                location=item.get("candidate_required_location") or "Remote",
                salary=item.get("salary"),
                description=_clean_html(item.get("description", "")),
                requirements=_clean_html(item.get("description", ""))[:1200],
                tags=_list(item.get("tags")) + _list(item.get("category")),
                seniority=_infer_seniority(item.get("title", "")),
                remote=True,
                url=item.get("url"),
                external_id=str(item.get("id") or item.get("url")),
                source="remotive",
            )
            for item in jobs[: request.limit]
        ]

    async def _adzuna(self, request: JobImportRequest) -> list[JobCreate]:
        if not self.settings.adzuna_app_id or not self.settings.adzuna_app_key:
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY are required for Adzuna ingestion")
        params = {
            "app_id": self.settings.adzuna_app_id,
            "app_key": self.settings.adzuna_app_key,
            "results_per_page": request.limit,
            "what": request.query or "",
            "where": request.location or "",
            "content-type": "application/json",
        }
        url = f"https://api.adzuna.com/v1/api/jobs/{self.settings.adzuna_country}/search/1"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        jobs = response.json().get("results", [])
        return [
            JobCreate(
                title=item.get("title") or "Untitled role",
                company=(item.get("company") or {}).get("display_name") or "Unknown company",
                location=(item.get("location") or {}).get("display_name") or request.location or "Unspecified",
                salary=_salary(item),
                description=_clean_html(item.get("description", "")),
                requirements=_clean_html(item.get("description", ""))[:1200],
                tags=_keywords(item.get("title", ""), item.get("description", "")),
                seniority=_infer_seniority(item.get("title", "")),
                remote=_looks_remote(item.get("title", ""), item.get("description", ""), request.location or ""),
                url=item.get("redirect_url"),
                external_id=str(item.get("id") or item.get("redirect_url")),
                source="adzuna",
            )
            for item in jobs[: request.limit]
        ]

    async def _greenhouse(self, request: JobImportRequest) -> list[JobCreate]:
        if not request.company:
            raise ValueError("company is required for Greenhouse ingestion")
        url = f"https://boards-api.greenhouse.io/v1/boards/{request.company}/jobs"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"content": "true"})
            response.raise_for_status()
        jobs = response.json().get("jobs", [])
        normalized = []
        for item in jobs[: request.limit]:
            location = (item.get("location") or {}).get("name") or "Unspecified"
            description = _clean_html(item.get("content", ""))
            normalized.append(
                JobCreate(
                    title=item.get("title") or "Untitled role",
                    company=request.company,
                    location=location,
                    salary=_greenhouse_pay(item),
                    description=description,
                    requirements=description[:1200],
                    tags=_keywords(item.get("title", ""), description),
                    seniority=_infer_seniority(item.get("title", "")),
                    remote=_looks_remote(item.get("title", ""), description, location),
                    url=item.get("absolute_url"),
                    external_id=str(item.get("id") or item.get("absolute_url")),
                    source="greenhouse",
                )
            )
        return normalized

    async def _lever(self, request: JobImportRequest) -> list[JobCreate]:
        if not request.company:
            raise ValueError("company is required for Lever ingestion")
        url = f"https://api.lever.co/v0/postings/{request.company}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params={"mode": "json"})
            response.raise_for_status()
        jobs = response.json()
        normalized = []
        for item in jobs[: request.limit]:
            categories = item.get("categories") or {}
            lists = item.get("lists") or []
            description = _clean_html(
                " ".join(
                    [item.get("descriptionPlain") or item.get("description") or ""]
                    + [section.get("content", "") for section in lists]
                )
            )
            location = categories.get("location") or "Unspecified"
            normalized.append(
                JobCreate(
                    title=item.get("text") or "Untitled role",
                    company=request.company,
                    location=location,
                    salary=None,
                    description=description,
                    requirements=description[:1200],
                    tags=_list(categories.get("team")) + _list(categories.get("commitment")) + _keywords(item.get("text", ""), description),
                    seniority=_infer_seniority(item.get("text", "")),
                    remote=_looks_remote(item.get("text", ""), description, location),
                    url=item.get("hostedUrl") or item.get("applyUrl"),
                    external_id=str(item.get("id") or item.get("hostedUrl")),
                    source="lever",
                )
            )
        return normalized


def _clean_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value or ""))).strip()


def _list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)]


def _salary(item: dict[str, Any]) -> str | None:
    minimum = item.get("salary_min")
    maximum = item.get("salary_max")
    if minimum and maximum:
        return f"{minimum:,.0f}-{maximum:,.0f}"
    return None


def _greenhouse_pay(item: dict[str, Any]) -> str | None:
    ranges = item.get("pay_input_ranges") or []
    if not ranges:
        return None
    first = ranges[0]
    currency = first.get("currency_type") or ""
    minimum = first.get("min_cents")
    maximum = first.get("max_cents")
    if minimum and maximum:
        return f"{currency} {minimum / 100:,.0f}-{maximum / 100:,.0f}"
    return None


def _infer_seniority(*parts: str) -> str | None:
    text = " ".join(parts).lower()
    mapping = {
        "intern": "internship",
        "entry": "entry",
        "junior": "entry",
        "associate": "entry",
        "senior": "senior",
        "staff": "staff",
        "principal": "principal",
        "lead": "lead",
        "director": "director",
    }
    return next((level for word, level in mapping.items() if word in text), None)


def _looks_remote(*parts: str) -> bool:
    text = " ".join(parts).lower()
    return "remote" in text or "work from home" in text or "anywhere" in text


def _keywords(*parts: str) -> list[str]:
    text = " ".join(parts).lower()
    skills = ["AI", "ML", "Python", "AWS", "React", "SQL", "Product Management", "Data", "Backend", "LLM", "RAG", "Fintech"]
    return [skill for skill in skills if skill.lower().replace(" management", "") in text]
