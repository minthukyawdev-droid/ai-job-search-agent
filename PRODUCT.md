# Job Search Agent — Product Direction

Status: proposed product baseline

Owner: product + engineering

Planning horizon: next 8 weeks

Last updated: 2026-07-03

## Product thesis

Active job seekers do not mainly need more job listings. They need a fast, trustworthy way to turn a large, noisy market into a small set of roles worth pursuing and to keep those pursuits moving.

The product should help a candidate answer three questions:

1. Which roles are worth my time?
2. Why does each role fit or not fit me?
3. What should I do next?

The initial product is a decision and workflow assistant, not an autonomous applicant. It should never imply that an external application was submitted when it only changed an internal status.

## Target customer

### Beachhead user

An active knowledge worker applying to 5–20 roles per week who:

- has at least one clear target role;
- searches across several job boards;
- wants remote or location-specific work;
- currently tracks opportunities in tabs, bookmarks, notes, or a spreadsheet; and
- values relevance and explainability more than the largest possible listing count.

The first release should optimize for individual candidates. Recruiters, career coaches, and fully autonomous application workflows are out of scope until the candidate loop works.

### Core job to be done

> When I am actively looking for my next role, help me quickly identify credible jobs that fit my goals and keep track of the next action, so I spend less time searching and more time pursuing good opportunities.

## Positioning

For active knowledge workers overwhelmed by fragmented job boards, Job Search Agent is a personal job-search workspace that ranks fresh roles against a candidate profile, explains the fit, and keeps the application pipeline organized.

Unlike a generic job board, it is profile-aware. Unlike a spreadsheet, it discovers and evaluates roles. Unlike an auto-apply bot, it keeps the candidate in control.

## Product principles

1. **Trust before magic.** Show source, freshness, constraints, and the reasons behind a match.
2. **One obvious next action.** Every state should guide the user to complete a profile, review a match, visit the source, or update the pipeline.
3. **Candidate control.** AI proposes and explains; the user decides.
4. **Outcomes over inventory.** Optimize for qualified opportunities and application progress, not raw jobs imported.
5. **Private by default.** Resume and profile data require explicit handling, deletion, and retention controls before public launch.

## Current product assessment

### What is already valuable

- Natural-language search with extracted role, skill, seniority, location, and remote filters.
- Profile-based recommendations with a visible score breakdown.
- Multiple ingestion sources plus deduplication.
- Saving and application-status tracking.
- A compact end-to-end interface covering discovery, job detail, profile, and pipeline.

### Highest-risk gaps

| Gap | User impact | Product decision |
| --- | --- | --- |
| “Apply” only marks a job as applied | Breaks trust and corrupts the tracker | Rename to “Mark applied”; make “Apply on source” the primary external action |
| Saving a profile always creates a new profile | Returning users lose continuity and create orphaned histories | Support one editable active profile before adding accounts |
| Setup order is implicit | New users hit empty recommendations and alerts | Add a guided profile → preferences → results onboarding path |
| Job importing appears in the candidate search UI | Exposes an operator concern and makes results feel broken | Move ingestion to a scheduled/admin workflow; give users a normal empty state |
| Match score lacks calibration | A precise percentage may imply unsupported certainty | Label as “fit estimate,” explain factors and missing requirements, measure usefulness |
| No event or outcome instrumentation | The team cannot learn whether matching helps | Instrument the core funnel before tuning ranking weights |
| No authentication or profile deletion | Unsafe for a public product containing resume data | Keep the current build in private beta until identity and deletion exist |
| Application states are too coarse | Users cannot see next action or follow-up timing | Add `interested`, `applied`, `interview`, `offer`, `rejected`, `withdrawn`, and next-action date |

## MVP journey

1. User lands on a clear promise and selects “Build my job profile.”
2. User adds target roles, skills, seniority, location/remote preference, and optionally a resume.
3. Product confirms the interpreted preferences and shows profile completeness.
4. User receives a small ranked feed of fresh jobs.
5. Each result shows fit evidence, possible gaps, source, and posting age.
6. User dismisses, saves, or opens the original listing.
7. After applying externally, user marks the role applied and sets a follow-up.
8. Product returns the user to the most useful next action.

The user should reach a credible first recommendation within three minutes.

## Success model

### North-star metric

**Weekly qualified opportunities (WQO):** unique jobs that a weekly active user saves or opens on the source after viewing the match explanation.

This measures whether the product turns inventory into credible opportunities. It should be paired with guardrails so low-quality clicks do not look like success.

### Funnel

| Stage | Event | Initial target |
| --- | --- | --- |
| Activation | Profile completed and at least 3 recommendations viewed in first session | ≥ 60% of new users |
| Match value | A recommendation is saved or opened on its source | ≥ 25% of recommendation viewers |
| Workflow adoption | User records at least one application | ≥ 30% of activated users within 7 days |
| Retention | Activated user returns in the following week | ≥ 25% |
| Outcome | User advances at least one application to interview | Baseline first; do not set a target before enough volume |

### Guardrails

- Recommendation dismissal rate and dismissal reason.
- Broken, duplicate, or expired listing report rate.
- Percentage of source opens that lead to a user-marked application.
- Time to first credible recommendation.
- Ranking latency and ingestion freshness.
- Resume deletion success and support incidents involving private data.

Targets are hypotheses for a private beta, not commitments. Revisit after 20 user interviews and at least 100 activated-user sessions.

## Instrumentation contract

Use stable event names and attach `user_id`, `session_id`, `job_id`, `source`, and timestamp where applicable. Do not send resume text or job-description content to analytics.

| Event | Required properties |
| --- | --- |
| `onboarding_started` | entry point |
| `profile_saved` | completion percentage, has_resume, target-role count |
| `recommendations_viewed` | result count, recommendation version |
| `match_explanation_opened` | job_id, rank, fit-estimate band |
| `job_saved` | job_id, rank, surface |
| `job_dismissed` | job_id, rank, reason |
| `job_source_opened` | job_id, rank, source |
| `application_status_changed` | job_id, previous status, new status |
| `follow_up_set` | job_id, days until follow-up |
| `job_reported` | job_id, reason |

## Prioritized roadmap

### Now — trustworthy private beta (weeks 1–2)

**P0. Correct application semantics**

- Replace “Apply” with “Apply on source” when a source URL exists.
- Opening the source must not automatically change application status.
- Provide a separate “Mark as applied” action with confirmation.
- Acceptance: no UI path claims an application was submitted by this product.

**P0. Persistent, editable profile**

- Update the active profile instead of creating a new record on every save.
- Load existing values when the user returns.
- Add explicit delete-profile behavior.
- Acceptance: editing a profile preserves its ID, saved jobs, and applications.

**P0. Guided activation**

- Make profile setup the default first-run path.
- Add fields for target seniority and remote preference.
- Confirm the interpreted preferences before recommendations.
- Acceptance: a first-time user can reach recommendations without knowing about imports or profile IDs.

**P0. Core analytics**

- Implement the events in the instrumentation contract.
- Add a small internal funnel report segmented by source.
- Acceptance: one test user can be followed from onboarding through source open without collecting resume contents.

**P0. Private-beta privacy baseline**

- Add authentication, ownership checks, profile deletion, and a short data-use notice.
- Acceptance: one user cannot read or mutate another user’s profile or pipeline.

### Next — useful weekly workflow (weeks 3–5)

**P1. Recommendation trust**

- Show posting date/freshness, matched evidence, likely gaps, and score bands.
- Add dismiss and report actions with reasons.
- Store the ranking version used for each impression.
- Acceptance: users can explain why a job appeared and remove bad results from their feed.

**P1. Pipeline with next actions**

- Add offer and withdrawn states.
- Add notes, next-action date, and follow-up reminders.
- Present saved jobs as a lightweight board or grouped list.
- Acceptance: every active application can have an owner-visible next step and date.

**P1. Background ingestion**

- Schedule imports, record provider health, and expire stale jobs.
- Remove provider import controls from the default candidate experience.
- Acceptance: recommendations populate without a candidate manually importing jobs.

**P1. Search control**

- Let users edit extracted filters and save searches.
- Preserve filters in shareable URLs.
- Acceptance: a user can correct a misunderstood query without rewriting it.

### Later — differentiated assistance (weeks 6–8+)

**P2. Daily or weekly job digest**

- Notify only for new jobs above a user-controlled fit threshold.
- Track notification-to-qualified-opportunity conversion.

**P2. Application preparation**

- Generate a requirements checklist and tailored resume suggestions.
- Require explicit user review; never fabricate experience or submit automatically.

**P2. Learning-to-rank experiments**

- Use saves, dismissals, source opens, and application progress as signals.
- Run ranking changes as versioned experiments with relevance guardrails.

## First research sprint

Recruit 8–10 active job seekers from the beachhead segment. Observe, rather than only ask about, their current workflow.

Key questions:

1. How do they decide that a listing is worth opening?
2. Which missing or incorrect detail destroys trust fastest?
3. What do they do after saving a role?
4. Do they understand the fit explanation and disagree with it appropriately?
5. Would they return for discovery, tracking, or both?

Prototype test:

- Give users five ranked jobs, including one intentionally questionable match.
- Ask them to think aloud, choose two to pursue, and explain why.
- Success means at least 7 of 10 correctly distinguish strong from questionable matches and can state what the score represents.

## Explicit non-goals for this horizon

- One-click or autonomous application submission.
- Recruiter or employer tooling.
- Cover-letter generation as the main value proposition.
- Social networking features.
- Maximizing the number of providers before freshness and quality are measurable.
- Native mobile apps before weekly web retention is demonstrated.

## Decision log

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-07-03 | Focus on active individual job seekers | The existing discovery and tracking loop already serves this user; multi-sided expansion would dilute learning |
| 2026-07-03 | Treat external application as user-controlled | The product cannot currently verify or submit an application and must not imply otherwise |
| 2026-07-03 | Use WQO as the north star | It connects recommendation quality to meaningful candidate action without pretending that the product controls hiring outcomes |
| 2026-07-03 | Keep public launch out of scope until identity and deletion ship | Resume text and pipeline data are sensitive |
