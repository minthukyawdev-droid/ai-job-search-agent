"use client";

import { useState } from "react";
import { DownloadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { importRealJobs } from "@/lib/api";

export function ImportJobsButton({ query }: { query: string }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function importJobs() {
    if (!query.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      const result = await importRealJobs(query);
      setMessage(`Imported ${result.imported}, updated ${result.updated} from ${result.source}.`);
      router.refresh();
    } catch {
      setMessage("Could not import real jobs right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <button className="button secondary" type="button" onClick={importJobs} disabled={loading || !query.trim()}>
        <DownloadCloud size={16} aria-hidden />
        {loading ? "Importing..." : "Import real jobs"}
      </button>
      {message ? <p className="snippet">{message}</p> : null}
    </div>
  );
}
