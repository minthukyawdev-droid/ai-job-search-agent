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
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "react": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "security": "Cybersecurity",
    "marketing": "Marketing",
    "sales": "Sales",
    "design": "Design",
    "analytics": "Analytics",
    "seo": "SEO",
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

LOCATION_ALIASES = {
    "us": "United States",
    "usa": "United States",
    "uk": "United Kingdom",
    "uae": "United Arab Emirates",
    "apac": "APAC",
    "emea": "EMEA",
    "latam": "LATAM",
}


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
        normalized = re.sub(r"\s+", " ", query).strip()
        lower = normalized.lower()
        tokens = tokenize(query)
        skills = []
        for token in tokens:
            skill = SKILL_ALIASES.get(token)
            if skill and skill not in skills:
                skills.append(skill)

        seniority = next((value.lower() for key, value in LEVEL_WORDS.items() if key in lower), None)
        remote = True if re.search(r"\b(remote|work from home|wfh|anywhere)\b", lower) else None
        if re.search(r"\b(on[- ]?site|office[- ]based)\b", lower):
            remote = False

        location = self._extract_location(normalized)
        role = self._extract_role(normalized)

        explicit_skills = re.search(
            r"\b(?:with|using|requiring|skills?[:\s]+)\s+(.+?)(?=\s+\b(?:in|near|across|for|at)\b|$)",
            normalized,
            flags=re.IGNORECASE,
        )
        if explicit_skills:
            for value in re.split(r",|/|\+|\band\b", explicit_skills.group(1), flags=re.IGNORECASE):
                clean = value.strip(" .-")
                if clean and len(clean.split()) <= 3:
                    canonical = SKILL_ALIASES.get(clean.lower(), clean.title())
                    if canonical not in skills:
                        skills.append(canonical)

        return SearchFilters(role=role, seniority=seniority, location=location, skills=skills, remote=remote)

    def _extract_location(self, query: str) -> str | None:
        match = re.search(
            r"\b(?:in|near|across|based in)\s+([A-Za-z][A-Za-z\s,-]{1,45}?)(?=\s+\b(?:with|using|requiring|for|at)\b|$)",
            query,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        location = re.sub(r"\b(remote|jobs?|roles?|positions?)\b", "", match.group(1), flags=re.IGNORECASE)
        location = re.sub(r"\s+", " ", location).strip(" ,-")
        if not location:
            return None
        return LOCATION_ALIASES.get(location.lower(), location.title())

    def _extract_role(self, query: str) -> str | None:
        role = re.split(r"\b(?:jobs?|roles?|positions?|openings?)\b", query, maxsplit=1, flags=re.IGNORECASE)[0]
        role = re.split(r"\b(?:in|near|across|with|using|requiring|at)\b", role, maxsplit=1, flags=re.IGNORECASE)[0]
        role = re.sub(r"\b(remote|work from home|wfh|on[- ]?site)\b", "", role, flags=re.IGNORECASE)
        for word in LEVEL_WORDS:
            role = re.sub(rf"\b{re.escape(word)}\b", "", role, flags=re.IGNORECASE)
        role = re.sub(r"\blevel\b", "", role, flags=re.IGNORECASE)
        role = re.sub(r"\s+", " ", role).strip(" ,-")
        role = re.sub(r"\bpm\b", "Product Manager", role, flags=re.IGNORECASE)
        role = re.sub(r"\bml\b", "Machine Learning", role, flags=re.IGNORECASE)
        if not role:
            return None
        titled = role.title()
        return re.sub(r"\bAi\b", "AI", titled)
