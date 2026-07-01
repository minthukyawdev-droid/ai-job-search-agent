"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { JobCard } from "@/components/JobCard";
import { getRecommendations, JobMatch } from "@/lib/api";
import { getStoredProfileId } from "@/lib/profile";

export default function RecommendationsPage() {
  const [jobs, setJobs] = useState<JobMatch[]>([]);
  const [message, setMessage] = useState("Loading recommendations...");

  async function load() {
    const userId = getStoredProfileId();
    if (!userId) {
      setMessage("Create a profile first to get recommendations.");
      return;
    }
    try {
      const data = await getRecommendations(userId);
      setJobs(data);
      setMessage(data.length ? "" : "No recommendations yet. Import jobs first.");
    } catch {
      setMessage("Could not load recommendations. Check that the backend is running.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Recommended for you</p>
        <h1>Ranked matches from your profile.</h1>
        <button className="button secondary" type="button" onClick={load}>
          <RefreshCw size={16} aria-hidden />
          Refresh
        </button>
      </section>
      <section className="stack">
        {message ? <div className="empty">{message}</div> : null}
        {jobs.map((job) => (
          <JobCard job={job} key={job.id} />
        ))}
      </section>
    </main>
  );
}
