# Sendhome — the updated winning idea

NextSpark Hacks 2026. Deadline Mon Oct 26, 10:00pm CDT. This is the idea after folding in all seven roadmap improvements.

## One-line pitch
Sendhome turns a hospital discharge sheet into a plain-language plan you can trust, because every line links back to the exact sentence in your original paperwork, and anything it can't verify is flagged "confirm with your nurse."

## The person and the moment
A patient or family caregiver leaves the hospital holding two dense pages: medication names and doses, warning signs, follow-up visits. They are tired, possibly reading in a second language, and a missed dose or missed warning sign is what sends people back to the ER. Sendhome is built for that moment, on a phone, in large type.

Do not put statistics in the Devpost text unless you have looked up and linked them yourself.

## What it does (the flow judges will see)
1. Paste the text of a discharge sheet (synthetic samples are built in as one-click examples).
2. Get back, in seconds:
   - A plain-language summary.
   - A medication table: name, dose, when, and why.
   - A "call your care team or go to the ER if..." list.
   - Follow-up appointments.
3. **Click any line** and the matching sentence in the original sheet is highlighted.
4. Anything the app could not match to the source is shown as **"Confirm with your nurse."**
5. Switch to a second language. Under it, a **back-translation into English** is shown side by side, so a reader who doesn't speak that language can still check it.
6. Ask questions. The answers come only from the document; anything else gets "That isn't in your paperwork — ask your nurse."
7. A computed **reading grade, before and after**, is shown on the result.

## The seven improvements, and what each one buys
| # | Feature | Judging payoff |
|---|---|---|
| 1 | Click-to-source highlighting on every output line | Technical Execution, Impact, Creativity. Grounding becomes visible instead of claimed |
| 2 | Verify pass: values not found in the source are flagged | Technical Execution, Impact. The honesty behavior is on screen |
| 3 | Back-translation under the translated copy | Demo, Technical Execution. English-only judges can check the translation |
| 4 | Reading grade before and after, computed | Impact. One measured number instead of adjectives |
| 5 | Mobile-first large type, plus read-aloud if time allows | UX. Fits the audience |
| 6 | Small accuracy check on 5 synthetic sheets, reported honestly | Technical Execution. Evidence over claims |
| 7 | Nothing stored; names and dates stripped before the API call if time allows | Impact. Answers the privacy question before it is asked |

## How it works (kept deliberately simple)
- Single-page web app plus one backend endpoint that calls an LLM API. The key lives in an environment variable and is never committed.
- The model returns structured JSON. Every item carries a `source_quote`, the verbatim sentence it came from.
- The verify pass checks that each `source_quote` actually appears in the input. Items that fail are flagged, not silently shown.
- The Q&A step is given only the document and instructed to refuse anything outside it. This should be tested with one in-document and one out-of-document question before recording.
- Translation is a separate call, and back-translation is a third call whose output is displayed beside it.
- Reading grade uses a standard readability formula computed locally.

## What is real and what is simulated (say this in the video and the Devpost text)
- **Real:** extraction, source linking, verification, grounded Q&A, translation, back-translation, reading-grade calculation.
- **Simulated or limited:** all sample documents are synthetic; there is no clinical validation; it is not medical advice and does not replace the care team.
- **Say plainly:** the accuracy check covers only 5 synthetic sheets and shows whatever it really showed, failures included.

## The unforgettable moment
The judge clicks "Take 1 tablet twice daily" and the matching sentence lights up in the original sheet, then asks a question the paperwork doesn't answer and watches the app refuse. That is the clip to build the video around.

## Video plan (1:30 to 2:30)
- 0:00–0:20: the person and the problem, with the dense sheet on screen.
- 0:20–1:30: live demo. Paste, result, click a line to see the source highlight, a flagged item, the translation with back-translation, one in-document question, one refused question.
- 1:30–2:00: the reading-grade number, the accuracy check, and the real-vs-simulated slide.
- Last 10 seconds: what you'd do next, said honestly as planned work, not as a feature.

## Build order and clock
| Time (CDT) | Work |
|---|---|
| 3:30–4:00 | Repo, README stub with the AI-tools section, 5 synthetic sheets, JSON schema |
| 4:00–5:15 | Extraction endpoint, verify pass, basic UI |
| 5:15–6:15 | Click-to-source highlighting, flagged-item state |
| 6:15–7:00 | Grounded Q&A, translation, back-translation |
| 7:00–7:45 | Reading grade, mobile layout, no-storage check |
| 7:45–8:15 | Accuracy check on the 5 sheets, results into the README |
| **8:15** | **Feature freeze** |
| 8:15–9:15 | Screenshots, video, README setup steps, fresh-clone test |
| 9:15–9:45 | Devpost submission, then open every link in a private window |
| 9:45–10:00 | Buffer only |

## If you fall behind, cut in this order
1. Read-aloud
2. Name and date stripping (keep "nothing is stored")
3. Reading-grade display (the formula is quick, so cut this last of the three)
4. Second language and back-translation, but only if highlighting and verification are not yet working

Never cut: extraction, click-to-source, the verify flag, grounded Q&A, and the required Devpost fields (public repo with setup instructions, public 1–3 minute video, at least one screenshot, tools and AI list).

## Risks
- A wrong dose or schedule on camera. Mitigation: test every sample sheet before recording and use the verify flag.
- Live LLM failure during recording. Mitigation: record from a pre-tested run.
- Overclaiming. Mitigation: the real-vs-simulated section above, copied into the Devpost text.
- Keys in the repo. Mitigation: `.env` gitignored and checked in git history before submitting.
