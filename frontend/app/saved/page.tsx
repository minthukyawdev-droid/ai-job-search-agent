"use client";

import { useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { Application, applyJob, getSavedJobs } from "@/lib/api";
import { getStoredProfileId } from "@/lib/profile";

const statuses = ["saved", "applied", "interview", "rejected"];

export default function SavedPage() {
  const [items, setItems] = useState<Application[]>([]);
  const [message, setMessage] = useState("Loading saved jobs...");

  async function load() {
    const userId = getStoredProfileId();
    if (!userId) {
      setMessage("Create a profile first to track jobs.");
      return;
    }
    try {
      const data = await getSavedJobs(userId);
      setItems(data);
      setMessage(data.length ? "" : "No saved jobs yet.");
    } catch {
      setMessage("Could not load saved jobs. Check that the backend is running.");
    }
  }

  async function update(jobId: number, status: string) {
    const userId = getStoredProfileId();
    if (!userId) return;
    await applyJob(userId, jobId, status);
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Application tracker</p>
        <h1>Saved and applied jobs.</h1>
      </section>
      <section className="stack">
        {message ? <div className="empty">{message}</div> : null}
        {items.map((item) => (
          <article className="card job-card" key={item.id}>
            <div className="job-head">
              <div>
                <h3>{item.job.title}</h3>
                <div className="company">
                  {item.job.company} · {item.job.location}
                </div>
              </div>
              <span className="score">{item.status}</span>
            </div>
            <div className="status-row">
              {statuses.map((status) => (
                <button
                  className={status === item.status ? "button" : "button secondary"}
                  type="button"
                  key={status}
                  onClick={() => update(item.job_id, status)}
                >
                  <CheckCircle2 size={16} aria-hidden />
                  {status[0].toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
