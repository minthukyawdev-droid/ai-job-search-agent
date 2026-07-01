"use client";

const PROFILE_KEY = "ai-job-search-profile-id";

export function getStoredProfileId(): number | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(PROFILE_KEY);
  return value ? Number(value) : null;
}

export function storeProfileId(id: number) {
  window.localStorage.setItem(PROFILE_KEY, String(id));
}
