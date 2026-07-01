import json
import re

from openai import OpenAI

from app.config import get_settings
from app.schemas import SearchFilters
from app.services.text import tokenize


SKILL_ALIASES = {
    "ai": "AI",
    "artificial": "AI",
    "machine": "Machine Learning",
    "ml": "Machine Learning",
    "product": "Product Management",
    "pm": "Product Management",
    "blockchain": "Blockchain",
    "crypto": "Blockchain",
    "fintech": "Fintech",
    "python": "Python",
    "sql": "SQL",
    "rag": "RAG",
    "llm": "LLM",
    "data": "Data",
    "growth": "Growth",
}

LEVEL_WORDS = {
    "entry": "Entry",
    "junior": "Entry",
    "associate": "Entry",
    "mid": "Mid",
    "senior": "Senior",
    "lead": "Lead",
    "principal": "Principal",
    "director": "Director",
}

LOCATION_PATTERNS = [
    "singapore",
    "apac",
    "remote",
    "india",
    "japan",
    "hong kong",
    "australia",
    "europe",
    "us",
    "usa",
    "united states",
]


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def parse_query(self, query: str) -> SearchFilters:
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.openai_chat_model,
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Extract job search filters as compact JSON with keys "
                                "role, location, skills, seniority, remote. Use null when unknown."
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                parsed = json.loads(content)
                if "level" in parsed and "seniority" not in parsed:
                    parsed["seniority"] = parsed["level"]
                return SearchFilters.model_validate(parsed)
            except Exception:
                pass
        return self._heuristic_parse(query)

    def explain_match(
        self,
        job_title: str,
        job_context: str,
        profile_context: str,
        matched_skills: list[str],
        location_match: bool,
        seniority_match: bool,
    ) -> str:
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.openai_chat_model,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an AI recruiter. Write one grounded explanation under 35 words. "
                                "Use only the supplied profile, job context, and match signals."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Job title: {job_title}\n"
                                f"Job context: {job_context[:1600]}\n"
                                f"User profile: {profile_context[:1600]}\n"
                                f"Signals: skills={matched_skills}, location_match={location_match}, "
                                f"seniority_match={seniority_match}"
                            ),
                        },
                    ],
                )
                return response.choices[0].message.content or ""
            except Exception:
                pass
        reasons = []
        if matched_skills:
            reasons.append(" + ".join(matched_skills[:4]))
        if location_match:
            reasons.append("location preference")
        if seniority_match:
            reasons.append("seniority fit")
        if reasons:
            return f"Matched because of {', '.join(reasons)}."
        return "Matched because the role context is semantically close to your search or profile."

    def _heuristic_parse(self, query: str) -> SearchFilters:
        lower = query.lower()
        tokens = tokenize(query)
        skills = []
        for token in tokens:
            skill = SKILL_ALIASES.get(token)
            if skill and skill not in skills:
                skills.append(skill)

        seniority = next((value.lower() for key, value in LEVEL_WORDS.items() if key in lower), None)
        remote = True if "remote" in lower else None
        location = None
        for pattern in LOCATION_PATTERNS:
            if re.search(rf"\b{re.escape(pattern)}\b", lower):
                location = "United States" if pattern in {"us", "usa"} else pattern.title()
                if pattern == "remote":
                    remote = True
                break

        role_terms = []
        stop_words = {"jobs", "job", "roles", "role", "in", "with", "like", "remote", "entry", "senior", "junior"}
        for token in tokens:
            if token not in stop_words and token not in SKILL_ALIASES and token not in LEVEL_WORDS:
                role_terms.append(token)
        role = " ".join(role_terms[:4]).title() or None

        if "product manager" in lower or "pm" in tokens:
            role = "AI Product Manager" if "ai" in tokens else "Product Manager"
        elif "engineer" in lower and ("ai" in tokens or "ml" in tokens):
            role = "AI Engineer"

        return SearchFilters(role=role, seniority=seniority, location=location, skills=skills, remote=remote)
