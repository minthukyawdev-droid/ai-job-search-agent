export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  salary?: string | null;
  description: string;
  requirements: string;
  tags: string[];
  seniority?: string | null;
  remote: boolean;
  source: string;
  url?: string | null;
  external_id?: string | null;
};

export type JobMatch = Job & {
  match_score: number;
  explanation: string;
  matched_skills: string[];
  score_breakdown: Record<string, number>;
};

export type SearchResponse = {
  filters: {
    role?: string | null;
    seniority?: string | null;
    location?: string | null;
    skills: string[];
    remote?: boolean | null;
  };
  results: JobMatch[];
};

export type ProfilePayload = {
  name: string;
  skills: string[];
  experience: string;
  preferred_roles: string[];
  location_preference: string;
  resume_text?: string | null;
};

export type Profile = ProfilePayload & {
  id: number;
};

export type Application = {
  id: number;
  user_id: number;
  job_id: number;
  status: string;
  notes?: string | null;
  match_score?: number | null;
  job: Job;
};

export type ImportJobsResponse = {
  source: string;
  imported: number;
  updated: number;
  jobs: Job[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function searchJobs(query: string) {
  return request<SearchResponse>(`/jobs/search?query=${encodeURIComponent(query)}`);
}

export function importRealJobs(query: string, source = "remotive") {
  return request<ImportJobsResponse>("/jobs/import", {
    method: "POST",
    body: JSON.stringify({ source, query, limit: 50 })
  });
}

export function getJob(id: string | number) {
  return request<Job>(`/jobs/${id}`);
}

export function saveProfile(payload: ProfilePayload) {
  return request<Profile>("/user/profile", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getRecommendations(userId: string | number) {
  return request<JobMatch[]>(`/recommendations/${userId}`);
}

export function saveJob(userId: number, jobId: number) {
  return request<Application>("/jobs/save", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, job_id: jobId })
  });
}

export function applyJob(userId: number, jobId: number, status = "applied") {
  return request<Application>("/jobs/apply", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, job_id: jobId, status })
  });
}

export function getSavedJobs(userId: string | number) {
  return request<Application[]>(`/jobs/saved/${userId}`);
}
