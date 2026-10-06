# Writing a lesson: the authoring brief

Every note in `content/notes/` is a **lesson that teaches its subtopic from the ground up** to a student pilot in
Western Australia who learns best visually. It is not a summary to revise from. A reader who has never met the
topic should finish the lesson understanding *why* things are so, able to do every calculation the syllabus names,
and knowing how the exam will ask about it. Read, in this order, before writing:

1. This brief.
2. The three exemplars, which set the bar: `notes/RBKA/3.6-stalling-spinning-and-spiral-dives.md` (a concept
   lesson), `notes/BAKC/6.2-take-off-and-landing-performance.md` (a calculation lesson),
   `notes/RFRC/2.3-conditions-of-flight.md` (a rules lesson).
3. The MOS wording for your subtopic: `python -m app.seed.show_elements UNIT n.n`. It governs what must be covered.
4. The current note for your subtopic: its facts, figures, references and visuals are the raw material to keep.
5. `content/README.md` (file format) and `content/diagrams/README.md` (how visuals are referenced).

## Structure

In this order. Headings are `##`; the page builds an "In this lesson" list from them, so make them meaningful
("Why the stall speed rises in a turn", not "3.6.3").

1. **Frontmatter**: `subtopic`, `title`, `references`. No `minutes` (study time is estimated from the text).
2. **`## What the exam expects (UNIT n.n)`**: first, always; one bullet per knowledge element with its number in
   bold (`**3.6.2**`). `check_content` fails without it. Paraphrase the MOS, do not copy it.
3. **`## Why this matters`**: three to six sentences. Where a WA student pilot meets this in real flying, and what
   the exam does with it. Concrete: a hot afternoon at Northam, a sea breeze at Jandakot, a Class D step at Perth.
4. **One section per knowledge element** or per coherent group of elements, each a teaching sequence:
   - open with a situation the reader can picture, or with something they already know;
   - explain the mechanism from first principles: the *why* before the *what*; define every term the first time
     it appears; one idea per paragraph; tables compare things, they never replace the explanation;
   - put a visual at the paragraph it illustrates (see Visuals);
   - `!!! example "Worked example"` for anything the element says to calculate, determine, extract or convert:
     step by step, every number with its unit, KaTeX for the maths, then a second example that varies what the
     exam varies (sign, direction, which quantity is unknown);
   - `!!! warning "Common trap"` for the misconception or the distractor the exam uses;
   - `??? check "Check yourself: …"` after the section it tests (see Self-checks).
5. **`## Bringing it together`**: where the subtopic lends itself to it, one short scenario that uses several
   elements at once (a flight from A to B, a go or no-go decision). Skip it when it would be forced.
6. **`## Key points`**: one memorable bullet per knowledge element. The reader should be able to reconstruct the
   lesson from these.
7. **`!!! tip "Exam tip"`**: last. How the exam asks about this subtopic and the figures to have by heart.

Length: **2,500 to 4,000 words** of body text, up to 4,500 for a subtopic with six or more knowledge elements.
Under that the lesson is a summary; over that, split the explanation into clearer sections or cut repetition.
`python -m app.seed.lint_lessons UNIT` reports the count (prose only: image references and callout header lines
are not counted).

## Prose

- Second person ("you"), plain words, short paragraphs. Write as a good instructor talks in a briefing room.
- Explain before you name: describe the thing, then give it its label in bold. After that use the label.
- Build on what came before, inside the lesson and across lessons: link related lessons as `/notes/UNIT/n.n`
  (for example "see the lift formula in [BAKC 4.2](/notes/BAKC/4.2)").
- Analogies only when they are accurate and you say where they break down.
- Numbers: knots and feet, except runway lengths and visibility in metres and kilometres. Thousands with a comma
  (1,000 ft). Degrees as "degrees" in prose, `°` in maths and tables.
- Maths is KaTeX: `$V_s \times \sqrt{n}$` inline, `$$ … $$` on its own line for a formula or a worked line.
  Only for real maths; ordinary prose and tables stay plain.
- No filler ("it is important to note"), no hedging about the subject itself, no exclamation marks.

## Accuracy

- **Never invent a figure.** Regulatory numbers (heights, distances, minima, times, codes) come from the current
  note or from the per-unit brief you were given. Keep the note's source citation next to the number and its
  "verify against the current AIP / Part 91 MOS / VFRG" flag. If you believe a figure in the old note is wrong,
  do not change it: report it.
- Physical and performance figures (ISA values, lapse rates, load factors) are the standard textbook values.
  Rules of thumb are labelled as such ("about", "roughly").
- Every worked example is arithmetic you have checked. Show the intermediate steps so the reader can check too.
- The POH wins: where a procedure is type-specific (spin recovery, carburettor heat), say so.

## Visuals

- Reference the unit's existing diagrams and widgets at the paragraph each one illustrates:
  `![Question the visual answers?](diagram:slug "What to notice: the one insight.")` or `widget:slug`. The
  caption is a question. Never inside the "What the exam expects" list and never inside a `??? check` answer.
- At least two visuals per lesson, three to five is typical, more for calculation-heavy subtopics. A visual can
  be used by more than one lesson if it fits both.
- Where the explanation wants a visual that does not exist, write the paragraph as if it were there and list the
  visual in your report with a one-line spec (what question it answers, what it shows). A visuals agent builds
  it afterwards from `tools/diagrams/AUTHORING.md`. Do not create diagram or widget files yourself.

## Worked examples

`!!! example "Worked example: <what it finds>"`. Inside: the given values as a short list, then numbered steps,
each one line of maths with the result in bold, then one sentence on what the answer means for the pilot.
Choose values the reader could meet in WA. Do not reuse the numbers of a quiz-bank question for the same
subtopic (`content/questions/`): the quiz tests what the lesson taught, so they must be different problems.
For a second example the reader should try first, state the problem in prose and put the working in
`??? solution "Show the solution"`.

Formulas are registered in `content/equations.yaml`, not marked in the lesson: when a lesson introduces a formula
the exam uses, add (or extend) its record there, with this lesson's id in `lessons` and figures that match the
lesson. Report any formula you added so it can be checked.

## Self-checks

`??? check "Check yourself: <the question>"` with the answer indented beneath. Three to six per lesson, placed
after the section each one tests, with one or two at the end that join elements together. They are short recall or
one-step reasoning questions ("Power on: does the stall IAS go up, down or stay the same, and why?"), never a
multi-step calculation (that is a worked example) and never a copy of a quiz-bank question. The answer is one to
three sentences and says *why*.

## Callouts

Only these have styling; the lint flags anything else.

| Markdown | Use |
|---|---|
| `!!! example "Worked example: …"` | step-by-step calculation |
| `!!! warning "Common trap"` | misconception or exam distractor |
| `!!! tip "Exam tip"` | the closing exam note |
| `??? check "Check yourself: …"` | self-check, answer hidden |
| `??? solution "Show the solution"` | hidden working for a try-it-first example |

Indent the body of a callout by four spaces; leave a blank line before and after the block.

## What a lesson is not

- Not a table of facts with a sentence of commentary. If the old note was a table, the lesson explains each row
  and may keep the table as the recap.
- Not a list of bullet points. Bullets are for genuinely parallel items (steps of a procedure, key points).
- Not the quiz. Self-checks and examples teach; the quiz bank tests.
- Not an encyclopaedia. Stay inside the MOS elements; depth, not breadth.

## Checks before you report

```
.venv/bin/python -m app.seed.check_content          # no PROBLEM lines for your files
.venv/bin/python -m app.seed.lint_lessons UNIT      # your lessons clean, or each warning explained in the report
```

## Report back

For each lesson: path, word count, visuals referenced, new visuals wanted (slug suggestion, the question it
answers, what it shows, which section), and anything in the old note you believe is wrong (with your reasoning).
Then any lint warning you left in place and why. Do not commit.
