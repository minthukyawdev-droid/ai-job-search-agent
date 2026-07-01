"use client";

import { Bookmark, Briefcase, CheckCircle2, ExternalLink, MapPin } from "lucide-react";
import Link from "next/link";
import { applyJob, JobMatch, saveJob } from "@/lib/api";
import { getStoredProfileId } from "@/lib/profile";

type Props = {
  job: JobMatch;
  showActions?: boolean;
};

export function JobCard({ job, showActions = true }: Props) {
  async function handleSave() {
    const userId = getStoredProfileId();
    if (!userId) {
      alert("Create a profile first so saved jobs can be tied to you.");
      return;
    }
    await saveJob(userId, job.id);
    alert("Saved");
  }

  async function handleApply() {
    const userId = getStoredProfileId();
    if (!userId) {
      alert("Create a profile first so applications can be tracked.");
      return;
    }
    await applyJob(userId, job.id, "applied");
    alert("Marked as applied");
  }

  return (
    <article className="card job-card">
      <div className="job-head">
        <div>
          <h3>
            <Link href={`/job/${job.id}`}>{job.title}</Link>
          </h3>
          <div className="company">{job.company}</div>
        </div>
        <span className="score">{job.match_score}%</span>
      </div>
      <div className="meta">
        <span className="pill">
          <MapPin size={14} aria-hidden />
          {job.location}
        </span>
        {job.seniority ? (
          <span className="pill">
            <Briefcase size={14} aria-hidden />
            {job.seniority}
          </span>
        ) : null}
        {job.remote ? <span className="pill">Remote</span> : null}
        <span className="pill">Source: {job.source}</span>
        {job.tags.slice(0, 4).map((tag) => (
          <span className="pill" key={tag}>
            {tag}
          </span>
        ))}
      </div>
      <p className="snippet">{job.explanation}</p>
      <details className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
        <summary className="cursor-pointer font-bold text-slate-900">Why this match?</summary>
        <div className="mt-3 grid gap-2 sm:grid-cols-4">
          {Object.entries(job.score_breakdown ?? {}).map(([key, value]) => (
            <span className="pill" key={key}>
              {key.replaceAll("_", " ")}: {Math.round(Number(value) * 100)}%
            </span>
          ))}
        </div>
      </details>
      {showActions ? (
        <div className="status-row">
          <button className="button secondary" type="button" onClick={handleSave} title="Save job">
            <Bookmark size={16} aria-hidden />
            Save
          </button>
          <button className="button" type="button" onClick={handleApply} title="Mark as applied">
            <CheckCircle2 size={16} aria-hidden />
            Apply
          </button>
          {job.url ? (
            <Link className="button secondary" href={job.url} target="_blank" rel="noreferrer" title="Open original posting">
              <ExternalLink size={16} aria-hidden />
              Source
            </Link>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
