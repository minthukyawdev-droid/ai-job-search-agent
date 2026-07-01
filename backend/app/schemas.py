from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str
    company: str
    location: str
    salary: str | None = None
    description: str
    requirements: str
    tags: list[str] = Field(default_factory=list)
    seniority: str | None = None
    remote: bool = False
    url: str | None = None
    external_id: str | None = None
    source: str = "json"


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: int

    class Config:
        from_attributes = True


class SearchFilters(BaseModel):
    role: str | None = None
    seniority: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    remote: bool | None = None

    @property
    def level(self) -> str | None:
        return self.seniority


class JobMatch(JobRead):
    match_score: float
    explanation: str
    matched_skills: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class UserProfileCreate(BaseModel):
    name: str
    skills: list[str] = Field(default_factory=list)
    experience: str = ""
    preferred_roles: list[str] = Field(default_factory=list)
    location_preference: str = ""
    resume_text: str | None = None


class UserProfileRead(UserProfileCreate):
    id: int

    class Config:
        from_attributes = True


class SaveJobRequest(BaseModel):
    user_id: int
    job_id: int
    notes: str | None = None


class ApplyJobRequest(SaveJobRequest):
    status: str = "applied"


class ApplicationRead(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: str
    notes: str | None = None
    match_score: float | None = None
    job: JobRead

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    filters: SearchFilters
    results: list[JobMatch]


class JobImportRequest(BaseModel):
    source: str = Field(description="json, remotive, adzuna, greenhouse, or lever")
    query: str | None = None
    company: str | None = Field(default=None, description="Greenhouse or Lever board token/company slug")
    location: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    jobs: list[JobCreate] | None = None


class ImportResponse(BaseModel):
    source: str
    imported: int
    updated: int
    jobs: list[JobRead]
