import { SearchBox } from "@/components/SearchBox";

export default function HomePage() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Hybrid AI search for serious job hunting</p>
        <h1>Find roles by describing the work you want.</h1>
        <p className="lead">
          Search naturally, rank jobs by fit, understand why each role matches, and keep your application pipeline organized.
        </p>
        <SearchBox />
      </section>
      <section className="grid">
        <div className="card">
          <h2>Recommended workflow</h2>
          <p className="snippet">
            Import the sample jobs, create a profile, then use the recommendations dashboard to rank roles against your skills,
            preferred roles, location, and resume text.
          </p>
        </div>
        <div className="card">
          <h2>Search examples</h2>
          <div className="stack">
            <span className="pill">entry level AI jobs in Singapore</span>
            <span className="pill">remote fintech product roles</span>
            <span className="pill">AI PM with blockchain experience</span>
          </div>
        </div>
      </section>
    </main>
  );
}
