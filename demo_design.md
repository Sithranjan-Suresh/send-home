# Sendhome — Phase 4: Demo design

Designed before implementation. Everything in the product exists to serve this demo. Numbers in angle brackets are filled in from a real test run before recording; do not invent them.

## Demo hook (first 15 seconds)
A close-up of a dense two-page discharge sheet, then one line of voiceover: "This is what a patient is handed on the way out of the hospital. Sendhome makes it readable — and shows its work."

## Demo flow
1. Dense sheet on screen (the built-in "Pneumonia" sample). State the person: a tired caregiver, reading on a phone.
2. Click "Use sample", then "Make it clear." Results appear: summary, medication table, "call or go to the ER" list, follow-ups.
3. Click one medication row. The matching sentence highlights in the original sheet.
4. Point to the heart-failure sample's medication with no dose listed, shown as "Dose not listed — confirm with your nurse."
5. Switch to Spanish. The Spanish text appears beside its English back-translation.
6. Ask an in-document question (e.g. "When do I see my doctor?"). It answers and highlights the source.
7. Ask an out-of-document question (e.g. "Can I take ibuprofen too?"). It replies: "That isn't in your paperwork — ask your nurse."
8. Show the reading grade before and after, then the accuracy check table from the README.
9. Close on the real-versus-simulated slide.

## Wow moments (4)
1. **Click-to-source highlight:** a plain-language line lights up the exact original sentence.
2. **The honest flag:** "Dose not listed — confirm with your nurse" instead of a guessed dose.
3. **The refusal:** the app declines an out-of-document question.
4. **Back-translation:** the viewer can check a language they don't read.

(The reading-grade drop is the supporting number, not a wow moment.)

## Required screens (only these)
1. Input screen: paste box, three sample buttons, one-line synthetic/not-medical-advice banner.
2. Results screen: summary, medication table, red flags, follow-ups, reading-grade badge.
3. Source panel: the original text with highlight, visible alongside results.
4. Translate view: translated text beside back-translation.
5. Ask box: question field, answer, source highlight or refusal.

No login, no history, no settings, no dashboard.

## User journey (judge's experience)
The judge opens the video and sees a real-looking sheet. In under 30 seconds they have watched it become a plan, clicked a line and seen where it came from, and seen the app refuse to guess. They finish the video knowing who it's for and why it can be trusted more than a generic summarizer.

## Judge takeaways (exactly three)
1. **Built for one moment and one person:** the patient or caregiver leaving the hospital.
2. **Every line is checkable:** it links to the source, and anything unverified is flagged.
3. **It is honest:** it says what it doesn't know and reports its own test results, including failures.

## Ideal 90-second demo script
Timings are approximate; read at a normal pace. Replace <X>, <Y>, <n>, <m> with real values from the last test run.

**[0:00–0:15]** "Leaving the hospital means leaving with two crowded pages of instructions: medicines, doses, warning signs. If you're tired, worried, or reading in a second language, it's easy to miss something that matters. This is Sendhome."

**[0:15–0:35]** "I paste a discharge sheet. This one is synthetic — I'll come back to that. One click, and I get a plain-language summary, a medicine table, the signs that mean call your care team or go to the ER, and my follow-up visits."

**[0:35–0:50]** "Here's what makes it different. I click this medicine, and the exact sentence in the original paperwork lights up. Nothing is a guess I can't check."

**[0:50–1:05]** "And when the paperwork doesn't say something, Sendhome doesn't invent it. This medicine has no dose listed, so it says: confirm with your nurse."

**[1:05–1:20]** "Switch to Spanish. Beside it, the app translates its own Spanish back into English, so you can check a language you don't read."

**[1:20–1:35]** "I ask when I see my doctor, and it answers from the sheet and shows where. I ask something the sheet doesn't cover, and it says: that isn't in your paperwork, ask your nurse."

**[1:35–1:50]** "The text moves from a reading grade of <X> to about <Y>. On five synthetic test sheets, it found <n> of <m> expected medicines, and I list the misses in the README."

**[1:50–2:05]** "Everything here is synthetic, it isn't medical advice, and it doesn't replace your care team. Sendhome: a discharge plan you can check."

(About 2 minutes, within the 1–3 minute limit. If it runs long, cut the line about Spanish first.)
