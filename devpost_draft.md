# Devpost draft — Sendhome

**Title:** Sendhome

**Tagline:** A discharge plan you can check — every line links to the sentence it came from.

## Inspiration
People leave the hospital with two dense pages of medicines, doses, warning signs and follow-ups, often tired, anxious, or reading in a second language. A generic AI summary reads fluently but can't be checked. We wanted a tool where trust matters more than fluency.

## What it does
Paste a (synthetic) discharge sheet and get a plain-language summary, a medicine table, "call your care team" and "go to the ER" lists, and follow-up visits. Click **Show source** on any line and the exact sentence in the original lights up. When the paperwork doesn't say something, Sendhome says so ("Dose not listed — confirm with your nurse") instead of guessing. You can view the plan in Spanish next to an independent English back-translation, and ask questions that are answered only from the paperwork; anything else gets "That isn't in your paperwork — ask your nurse." A **Break it** button proves the checker works: it corrupts a dose and adds a false line, and the server flags both. **Official label:** for any medicine, Anakin fetches the official MedlinePlus page and we show a word-for-word excerpt and link, clearly labelled as not from the paperwork. A reading grade is shown for the original and the plain-language output.

## How we built it
FastAPI backend (stateless, nothing stored) and a plain HTML/JS frontend. The model must return a verbatim `source_quote` for every item; deterministic code then locates each quote in the original (exact, normalized, then best-sentence similarity) and flags what it can't find. Refusals are enforced in code: if the model says the answer isn't in the document, or its supporting quotes can't be found, the server returns the fixed refusal text. The back-translation is a separate call that only sees the Spanish. LLM: Groq-hosted models (openai/gpt-oss-120b, falling back to gpt-oss-20b and qwen3.8-27b when the free daily token cap is hit). The three built-in samples ship with saved results from a real run (labelled as such in the UI) so the demo works instantly and offline; anything you paste goes to the live model.

## How we use Anakin
Anakin's web-data API fetches the official MedlinePlus page for each medicine on demand. Our code then extracts word-for-word excerpts, so even web information gets the same checkable-quote treatment as the paperwork. Only the generic medicine name is sent to Anakin, never the patient's text. If no official page matches (for example docusate), the app says so instead of guessing.

## Real vs simulated
- **Real:** extraction, source linking, verification, grounded Q&A, translation, back-translation, reading-grade calculation.
- **Simulated / limited:** every sample document is synthetic; no clinical validation; not medical advice; Spanish is machine-generated and unreviewed.

## How we measured it
On five synthetic sheets (hand-labelled expectations), the final prompts found 19/19 expected medicines and 37/37 warning-sign keywords in all three runs; doses were right 18/19 in one run and 19/19 in the other two. Grounded Q&A handled 12/12 test questions correctly in one run. The reading grade dropped on every sheet in the final runs. This is a small self-check on invented documents, and our README lists the misses, the earlier failed run, and what we changed.

## Challenges
Groq's free tier has a daily token cap that our own evaluation runs nearly used up. We added model fallback, saved real-run results for the built-in samples (clearly labelled), and a clear message when limits are hit.

Our first sample sheets were too plain, so the reading grade didn't drop. We rewrote them realistically and kept the first-run results in the repo. The model also intermittently dropped a whole group of warning signs until we added an explicit completeness rule.

## What's next (ideas, not features)
Photo/PDF input with OCR; more languages reviewed by native speakers; a clinician review mode and testing on real de-identified documents under proper approvals.

## Built with
Python, FastAPI, Pydantic, httpx, pytest, HTML/CSS/JavaScript, Groq (openai/gpt-oss-120b, gpt-oss-20b, qwen3.8-27b), Anakin (anakin.io) for official-label lookups via MedlinePlus. Built with the help of Claude Code (AI coding assistant).

## Links
- Try it live: https://sendhome-uhw9.onrender.com (free hosting; the first load after a pause can take about a minute)
- Repo: https://github.com/Sithranjan-Suresh/send-home
- Video: _(add after recording)_
