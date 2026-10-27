# Sendhome: 2-minute video script and submission checklist

Target length: about 2:00 (limit is 1-3 minutes). Record at a clean desktop size, browser zoom 100%, no other tabs visible. Speak at a normal pace. Every number below is real and comes from this repo.

## Before you hit record (5 minutes)

1. Start the app: `python -m uvicorn backend.app:app --port 8000`, open <http://localhost:8000>, hard-refresh (Ctrl+Shift+R).
2. You do NOT need an AI key for this script: the three sample sheets use saved results from a real run, and the official labels for their medicines are saved too.
3. Click "Try a sample sheet" once as a rehearsal, then reload so you start on the hero.
4. Close notifications. Hide bookmarks. Make the browser window wide (1280px or more) so the source pane sits beside the results.
5. Do one practice run of the whole script before recording.

## The script (about 2:00)

**[0:00-0:15] Hero. The problem.**
On screen: the hero with the animated sheet (wait for the highlight and the two bubbles).
Say: "Leaving the hospital means leaving with two crowded pages: medicines, doses, warning signs. If you're tired or worried, it's easy to miss something. A normal AI summary reads fluently, but you can't check it. This is Sendhome: paperwork you can check."

**[0:15-0:35] One click, plain plan.**
Click **Try a sample sheet**. The results appear.
Say: "One click turns this synthetic discharge sheet into a plain-language plan: medicines, warning signs, follow-ups. And the reading level drops from grade 11.8 to 5.8."
Point to the green bar: "Twenty of twenty lines found in the original paperwork."

**[0:35-0:50] Click to source.**
Click **Show source** on a medicine row. The sentence highlights in the original on the right.
Say: "Every line links to the exact sentence it came from. The AI has to quote the paperwork word for word, and code, not the AI, checks the quote is really there."

**[0:50-1:05] Missing stays missing.**
Click **Heart failure**, then **Make it clear**. Scroll to the metoprolol row.
Say: "When the paperwork doesn't say something, Sendhome doesn't invent it. This medicine has no dose listed, so it says: confirm with your nurse."

**[1:05-1:20] Questions stay on the page.**
Go back to Pneumonia (Make it clear), scroll to Ask. Click "When do I see my doctor?", then "Can I take ibuprofen too?".
Say: "Ask something the sheet answers and it shows where. Ask something it doesn't cover and it refuses: that isn't in your paperwork, ask your nurse. The refusal is enforced in code, not left to the AI's wording."

**[1:20-1:40] Break it. The proof.**
Scroll to the verified-lines bar. Click **Break it**.
Say: "Don't take our word for it. I'll corrupt the plan: this multiplies a dose by ten and adds a dangerous false line. The same checker re-reads the original paperwork and catches both. Two of two."
Click **Restore original**.

**[1:40-1:55] Official label, powered by Anakin.**
Scroll to the medicines table. Click **Official label** on amoxicillin-clavulanate.
Say: "For any medicine, Anakin fetches the official MedlinePlus page, and we show a word-for-word excerpt with a link, clearly marked as not from your paperwork. Only the medicine name is sent. The same rule applies: quote it, don't paraphrase it."

**[1:55-2:15] Honest numbers and the close.**
Click **Report card** in the nav.
Say: "On five synthetic test sheets it found nineteen of nineteen medicines and thirty-seven of thirty-seven warning-sign keywords, and eighteen of nineteen doses. The misses and the earlier failed runs are listed. Everything here is synthetic, it isn't medical advice, and it doesn't replace your care team. Sendhome: a discharge plan you can check."

If you run long, cut the Spanish (not shown above), then the Ask section. Never cut Break it.

## Numbers you can say (all real)

| Claim | Value | Where it comes from |
|---|---|---|
| Reading grade, pneumonia sample | 11.8 to 5.8 | Saved run, shown on the results page |
| Lines found in the paperwork | 20 of 20 | Verified-lines bar on the pneumonia sample |
| Medicines found, 5 sheets | 19 of 19 | Report card, Run 1 (`gpt-oss-120b`) |
| Doses correct, 5 sheets | 18 of 19 | Same run; runs 2 and 3 had 19 of 19 |
| Warning-sign keywords | 37 of 37 | All three final runs |
| Test questions handled | 12 of 12 | Run 1 |
| Break it | caught 2 of 2 | Live in the app |

Do not claim clinical validation, real-world accuracy, or that the Spanish is reviewed.

## Things to avoid on camera

- Do not paste real patient information. Use only the built-in samples.
- Do not show `.env` or any API key.
- Do not say the sample results are "live": the UI labels them "Saved result from a real run". If asked, say so. Pasted text always runs live.
- If the screen shows a rate-limit message when you paste your own text, wait 20 seconds and try again, or stick to the built-in samples.

## After recording

1. Upload the video (YouTube or Vimeo, set to public or unlisted-but-viewable). Open the link in a private window to confirm it plays without logging in.
2. Open the repo <https://github.com/Sithranjan-Suresh/send-home> in a private window. The README should show six screenshots.
3. Fill in Devpost from `devpost_draft.md`: title, tagline, description, real-vs-simulated, how we use Anakin, built-with list (including the AI-assistance disclosure), repo link, video link, and at least one screenshot from `docs/screenshots/`.
4. Check the official hackathon rules for any extra required field, track, or sponsor checkbox (Anakin).
5. Submit at least an hour before the 10:00 PM CDT deadline, then reopen the submission page and confirm it says submitted.
