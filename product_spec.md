# Sendhome — product_spec.md

## Product requirements (must be true at submission)
- A public web app, runnable locally from the README steps, that analyzes pasted discharge text.
- Three built-in synthetic sample sheets and two more used only for the accuracy check (5 total).
- A visible "synthetic samples only — not medical advice — don't paste real patient information" banner.
- No storage of user text. No accounts.
- All required Devpost fields complete.

## User stories and acceptance criteria

**S1 — As a caregiver, I want to load a sample or paste my paperwork so that I can try the app without typing.**
- Three sample buttons fill the text box.
- Pasted text up to 8,000 characters is accepted; longer input shows a clear message.

**S2 — As a caregiver, I want a plain-language plan so that I can understand what to do.**
- Result shows summary (up to 5 points), medication table, "call or go to the ER" list, follow-ups.
- Analysis returns within about 15 seconds for a normal sheet, with a visible loading state.

**S3 — As a caregiver, I want to see where each line came from so that I can trust it.**
- Every item shows a "Show source" action.
- Clicking highlights the matching sentence in the original text and scrolls to it.
- If a match can't be located, the item is flagged instead of linked.

**S4 — As a caregiver, I want missing information shown as missing so that I'm not misled.**
- A medication with no dose in the source shows "Dose not listed — confirm with your nurse."
- Any item whose quote is not found in the source shows "Couldn't verify — confirm with your nurse."
- Any dose with numbers not present in its quote is flagged.

**S5 — As a caregiver, I want to ask questions so that I can clarify things.**
- In-document questions get an answer plus a source highlight.
- Out-of-document questions get exactly: "That isn't in your paperwork — ask your nurse."
- The refusal text comes from code, not the model.

**S6 — As a Spanish-speaking family member, I want the plan in Spanish so that I can read it.**
- A language selector produces a Spanish version of the plan.
- A back-translation into English is shown beside it, produced from the Spanish text only.
- If numbers in the translation don't match the original, a warning is shown.
- A line states that the translation is machine-generated and unreviewed.

**S7 — As a judge, I want a measurable result so that I can judge the claim.**
- Reading grade (approximate) is shown for the original and for the plain-language output.
- The README includes an accuracy table from the 5-sheet check, including misses.

**S8 — As a phone user, I want large readable text so that I can use it comfortably.**
- Layout works at phone width with no horizontal scrolling; body text at least 18px.

**S9 (P2) — As a user, I want the plan read aloud so that I don't have to read it.**
- A button reads the summary using the browser's speech feature.

## Edge cases to handle
- Empty input, input over the limit, non-English input, or text that isn't a discharge sheet (show "This doesn't look like discharge instructions" instead of inventing content).
- Model returns invalid JSON: retry once, then show a clear error.
- LLM API error or timeout: show a retry message; never show partial output as complete.
- A quote that matches only after whitespace or punctuation normalization: still links.
- A quote that matches approximately: link to the best sentence if it is a close match, else flag.
- Duplicate medications or repeated sentences: highlight the first match and say so if ambiguous.
- Prompt-injection text inside the pasted document (e.g. "ignore previous instructions"): treat the document as data; the output must still follow the schema.

## Feature priority
**P0 (demo-blocking):** S1, S2, S3, S4, S5, banner, no storage, README with setup, video, screenshot.
**P1:** S6 (Spanish plus back-translation plus number check), S7 (reading grade and accuracy table), S8 (mobile layout).
**P2:** S9 read-aloud, client-side name and date stripping (regex-based; not a privacy guarantee), second language, live demo link, photo input.
