import { JobCard } from "@/components/JobCard";
import { ImportJobsButton } from "@/components/ImportJobsButton";
import { SearchBox } from "@/components/SearchBox";
import { searchJobs } from "@/lib/api";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const params = await searchParams;
  const query = params.q ?? "";
  const data = query ? await searchJobs(query).catch(() => null) : null;

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Natural language search</p>
        <h1>Search results</h1>
        <SearchBox initialQuery={query} />
        {query ? <ImportJobsButton query={query} /> : null}
      </section>
      {data ? (
        <section className="grid">
          <div className="stack">
            {data.results.length ? (
              data.results.map((job) => <JobCard job={job} key={job.id} />)
            ) : (
              <div className="empty">No jobs matched this search yet.</div>
            )}
          </div>
          <aside className="card">
            <h2>Extracted filters</h2>
            <div className="stack">
              <span className="pill">Role: {data.filters.role ?? "Any"}</span>
              <span className="pill">Seniority: {data.filters.seniority ?? "Any"}</span>
              <span className="pill">Location: {data.filters.location ?? "Any"}</span>
              <span className="pill">Remote: {data.filters.remote === true ? "Yes" : "Any"}</span>
              <span className="pill">Skills: {data.filters.skills.join(", ") || "Any"}</span>
            </div>
          </aside>
        </section>
      ) : (
        <div className="empty">Try a search like “senior AI PM remote jobs in APAC”.</div>
      )}
    </main>
  );
}
