"use client";

import { FormEvent, useState } from "react";
import { Save } from "lucide-react";
import { saveProfile } from "@/lib/api";
import { storeProfileId } from "@/lib/profile";

export default function ProfilePage() {
  const [message, setMessage] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const profile = await saveProfile({
      name: String(form.get("name") ?? ""),
      skills: split(String(form.get("skills") ?? "")),
      experience: String(form.get("experience") ?? ""),
      preferred_roles: split(String(form.get("preferred_roles") ?? "")),
      location_preference: String(form.get("location_preference") ?? ""),
      resume_text: String(form.get("resume_text") ?? "")
    });
    storeProfileId(profile.id);
    setMessage(`Profile saved. Active profile ID: ${profile.id}`);
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">User profile</p>
        <h1>Teach the matcher what good looks like.</h1>
      </section>
      <form className="card form-grid" onSubmit={onSubmit}>
        <label className="field">
          <span className="label">Name</span>
          <input className="input" name="name" required placeholder="Ada Lovelace" />
        </label>
        <label className="field">
          <span className="label">Location preference</span>
          <input className="input" name="location_preference" placeholder="Remote APAC" />
        </label>
        <label className="field">
          <span className="label">Skills</span>
          <input className="input" name="skills" placeholder="AI, Product Management, Blockchain" />
        </label>
        <label className="field">
          <span className="label">Preferred roles</span>
          <input className="input" name="preferred_roles" placeholder="AI Product Manager, Product Lead" />
        </label>
        <label className="field full">
          <span className="label">Experience</span>
          <textarea className="textarea" name="experience" placeholder="Summarize your recent roles, scope, and wins." />
        </label>
        <label className="field full">
          <span className="label">Resume text</span>
          <textarea className="textarea" name="resume_text" placeholder="Paste resume text for better recommendations." />
        </label>
        <div className="field full">
          <button className="button" type="submit">
            <Save size={16} aria-hidden />
            Save profile
          </button>
          {message ? <p className="snippet">{message}</p> : null}
        </div>
      </form>
    </main>
  );
}

function split(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
