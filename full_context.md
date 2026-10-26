# Sendhome — full_context.md

## Vision
**One sentence:** Sendhome turns a hospital discharge sheet into a plain-language plan where every line links back to its source sentence and anything unverifiable is flagged for a nurse.

**Paragraph:** Patients and caregivers leave the hospital with dense paperwork and little time to understand it. Existing AI summarizers produce fluent text that the reader cannot check. Sendhome's bet is that for health paperwork, trust matters more than fluency: every output line carries a verbatim quote from the original, missing information is shown as missing, and questions outside the document are refused. It is a hackathon prototype built on synthetic documents and is not medical advice.

## Problem
Discharge instructions are long, jargon-heavy and written for the hospital's liability as much as for the patient's comprehension. Readers who are tired, anxious, have low health literacy, or read English as a second language are most at risk of misreading doses or missing warning signs. A quantified statistic is intentionally not included here: add one only if you find it, link it, and have read the source. Otherwise leave numbers out of the Devpost text.

## Target users
- **Primary:** a patient or family caregiver on the day of discharge, usually on a phone.
- **Today:** they re-read the printout, search the web, or call a nurse line.
- **Why it's painful:** the printout can't be questioned, and a generic chatbot may answer confidently with things the paperwork never said.

## User journey (end to end)
Paste or pick a sample sheet, then press "Make it clear." Read the summary, medication table, red flags and follow-ups. Click any line to see its source sentence. Notice flagged items. Optionally switch to Spanish and compare against the back-translation. Ask follow-up questions, which are answered only from the document or refused.

## Core features (what exists at submission)
1. Analysis into structured sections (summary, medications, red flags, follow-ups), each item with a verbatim source quote.
2. Click-to-source highlighting.
3. Honest flags: missing fields are shown as missing; items whose quote can't be found in the source are flagged.
4. Grounded Q&A with a fixed refusal for anything not in the document.
5. Spanish translation with a back-translation panel and a numbers-match check.
6. Computed approximate reading grade before and after.
7. Mobile-first large-type layout.
8. Stateless: nothing is stored.
9. A small accuracy check on 5 synthetic sheets, reported honestly in the README.

Out of scope: photo or OCR input, accounts, history, real patient data, clinical validation.

## Key differentiators
- Verifiability: the reader can trace every line to the original, which a plain "summarize this" prompt does not offer.
- Honest uncertainty: missing doses stay missing, and out-of-document questions are refused by code, not by trusting the model's phrasing.
- Measured, self-reported results instead of adjectives.

## Technical overview
Python FastAPI backend with a single stateless API, a static HTML/JS frontend with no build step, and one LLM API (any chat-completions provider with JSON output; use the key you already have). The model returns structured JSON including verbatim quotes. Deterministic code (not the model) verifies quotes, finds highlight spans, checks numbers, and computes reading grade. Key technical bets: quote-then-verify instead of trusting generated text; refusal enforced in code; back-translation as a visible check.

## Demo flow
See `demo_design.md`.

## Success metrics
- **Product:** a judge can clearly see the three takeaways within 30 seconds of the video starting.
- **Technical:** all five sample sheets return schema-valid output; the verify pass catches a deliberately corrupted quote in a test; out-of-document questions are refused in the test run.
- **Submission:** public repo with working setup instructions, public 1–3 minute video, at least one screenshot, full tools and AI-assistance list, all links opened logged out.

## Future expansion (stated as ideas, not features)
1. Photo or PDF input with OCR.
2. More languages, with review by native speakers.
3. Clinician review mode, and testing on real de-identified documents under proper approvals.
