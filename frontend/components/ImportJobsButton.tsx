"use client";

import { useState } from "react";
import { DownloadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { importRealJobs } from "@/lib/api";
import type { ImportJobsOptions } from "@/lib/api";

export function ImportJobsButton({ query }: { query: string }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState<ImportJobsOptions["source"]>("remotive");
  const [company, setCompany] = useState("");

  const needsCompany = source === "greenhouse" || source === "lever";

  async function importJobs() {
    if (!query.trim() || (needsCompany && !company.trim())) return;
    setLoading(true);
    setMessage("");
    try {
      const result = await importRealJobs({ query, source, company: company.trim() });
      setMessage(`Imported ${result.imported}, updated ${result.updated} from ${result.source}.`);
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? `Import failed: ${error.message}` : "Could not import real jobs right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <div className="search-row">
        <select
          className="select"
          aria-label="Job provider"
          value={source}
          onChange={(event) => setSource(event.target.value as ImportJobsOptions["source"])}
        >
          <option value="remotive">Remotive</option>
          <option value="adzuna">Adzuna</option>
          <option value="greenhouse">Greenhouse</option>
          <option value="lever">Lever</option>
        </select>
        {needsCompany ? (
          <input
            className="input"
            aria-label="Company board slug"
            placeholder="Company board slug"
            value={company}
            onChange={(event) => setCompany(event.target.value)}
          />
        ) : null}
        <button
          className="button secondary"
          type="button"
          onClick={importJobs}
          disabled={loading || !query.trim() || (needsCompany && !company.trim())}
        >
          <DownloadCloud size={16} aria-hidden />
          {loading ? "Importing..." : "Load jobs"}
        </button>
      </div>
      {message ? <p className="snippet">{message}</p> : null}
    </div>
  );
}
