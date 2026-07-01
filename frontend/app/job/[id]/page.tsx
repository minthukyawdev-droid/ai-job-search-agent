import { Briefcase, ExternalLink, MapPin } from "lucide-react";
import Link from "next/link";
import { getJob } from "@/lib/api";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await getJob(id);

  return (
    <main className="page">
      <section className="detail-body">
        <div>
          <p className="eyebrow">{job.company}</p>
          <h1>{job.title}</h1>
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
          {job.salary ? <span className="pill">{job.salary}</span> : null}
          {job.remote ? <span className="pill">Remote</span> : null}
          {job.url ? (
            <Link className="button secondary" href={job.url} target="_blank" rel="noreferrer">
              <ExternalLink size={16} aria-hidden />
              View source
            </Link>
          ) : null}
        </div>
        <section className="card">
          <h2>Description</h2>
          <p className="snippet">{job.description}</p>
        </section>
        <section className="card">
          <h2>Requirements</h2>
          <p className="snippet">{job.requirements}</p>
        </section>
        <section className="card">
          <h2>Tags</h2>
          <div className="meta">
            {job.tags.map((tag) => (
              <span className="pill" key={tag}>
                {tag}
              </span>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
