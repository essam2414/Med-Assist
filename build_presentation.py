"""Build the Med Assist inspection presentation — ~25 slides.

Design rules:
  • Bigger text (body 14-16pt; bullet labels +1pt; headers 28pt).
  • Breathing room — 3-5 bullets per content slide; screenshot slides are dedicated.
  • Plain English where possible; technical detail kept where it matters (pipelines, RAG, model config).
  • Detail level matches the report.
  • Each AI feature gets pipeline + bugs/fixes + screenshot slides.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

OUT = "summaryPresentation.pptx"

# palette
NAVY    = RGBColor(0x0B, 0x2A, 0x4A)
NAVY2   = RGBColor(0x16, 0x3F, 0x67)
TEAL    = RGBColor(0x14, 0x8A, 0x9C)
ACCENT  = RGBColor(0xC2, 0x4D, 0x2C)
GOLD    = RGBColor(0xC9, 0x97, 0x1A)
GREEN   = RGBColor(0x2E, 0x7D, 0x32)
TEXT    = RGBColor(0x1B, 0x1F, 0x27)
MUTED   = RGBColor(0x55, 0x5C, 0x6A)
LIGHT   = RGBColor(0xF4, 0xF6, 0xFA)
SOFT    = RGBColor(0xEC, 0xF1, 0xF7)
PH_BG   = RGBColor(0xE6, 0xEA, 0xF1)
PH_LINE = RGBColor(0x9A, 0xA3, 0xB2)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
RED_BG  = RGBColor(0xFD, 0xF1, 0xEC)
GREEN_BG= RGBColor(0xEB, 0xF6, 0xEE)

SLIDE_W = Inches(13.3333)
SLIDE_H = Inches(7.5)


def set_run(run, text, *, size=15, bold=False, italic=False, color=TEXT):
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def add_textbox(slide, left, top, width, height, *, fill=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left   = Inches(0.10)
    tf.margin_right  = Inches(0.10)
    tf.margin_top    = Inches(0.06)
    tf.margin_bottom = Inches(0.06)
    if fill is not None:
        box.fill.solid()
        box.fill.fore_color.rgb = fill
    else:
        box.fill.background()
    box.line.fill.background()
    return box


def add_rect(slide, left, top, width, height, *, fill=NAVY):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill
    rect.line.fill.background()
    rect.shadow.inherit = False
    return rect


def add_title_bar(slide, title, subtitle=None):
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.95), fill=NAVY)
    add_rect(slide, Inches(0), Inches(0.95), SLIDE_W, Inches(0.06), fill=TEAL)
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.10), Inches(12.4), Inches(0.85))
    tf = box.text_frame; tf.margin_left = 0; tf.margin_top = 0; tf.word_wrap = True
    p = tf.paragraphs[0]
    set_run(p.add_run(), title, size=28, bold=True, color=WHITE)
    if subtitle:
        p2 = tf.add_paragraph(); p2.space_before = Pt(2)
        set_run(p2.add_run(), subtitle, size=14, italic=True,
                color=RGBColor(0xCF, 0xDB, 0xE8))


def add_footer(slide, page_num, total):
    f = slide.shapes.add_textbox(Inches(0.55), Inches(7.18), Inches(11.5), Inches(0.25))
    tf = f.text_frame; tf.margin_left = 0; tf.margin_top = 0
    p = tf.paragraphs[0]
    set_run(p.add_run(),
            "Med Assist  |  Essam Sheikh (2595328)  |  FYP Inspection",
            size=10, color=MUTED)
    pn = slide.shapes.add_textbox(Inches(12.3), Inches(7.18), Inches(0.85), Inches(0.25))
    tfp = pn.text_frame; tfp.margin_left = 0; tfp.margin_top = 0
    p2 = tfp.paragraphs[0]
    set_run(p2.add_run(), f"{page_num} / {total}", size=10, color=MUTED)
    p2.alignment = PP_ALIGN.RIGHT


def add_bullets(slide, left, top, width, height, items, *,
                size=15, label_size=None, gap=10, fill=None,
                label_color=NAVY):
    if label_size is None:
        label_size = size + 1
    box = add_textbox(slide, left, top, width, height, fill=fill)
    tf = box.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(0 if i == 0 else gap)
        if isinstance(item, tuple):
            label, body = item
            set_run(p.add_run(), f"•  {label}  ", size=label_size, bold=True,
                    color=label_color)
            set_run(p.add_run(), body, size=size, color=TEXT)
        else:
            set_run(p.add_run(), f"•  {item}", size=size, color=TEXT)
    return box


def add_image_placeholder(slide, left, top, width, height, label, *, accent=PH_LINE):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = PH_BG
    rect.line.color.rgb = accent
    rect.line.width = Pt(1.5)
    rect.line.dash_style = 7
    rect.shadow.inherit = False
    tf = rect.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.20); tf.margin_right = Inches(0.20)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    set_run(p.add_run(), "Screenshot", size=18, bold=True, color=MUTED)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(8)
    set_run(p2.add_run(), label, size=13, italic=True, color=MUTED)
    return rect


def add_callout(slide, left, top, width, height, text, *,
                fill=LIGHT, accent=TEAL, title=None, size=14):
    add_rect(slide, left, top, Inches(0.10), height, fill=accent)
    box = add_textbox(slide, left + Inches(0.20), top,
                      width - Inches(0.20), height, fill=fill)
    tf = box.text_frame
    tf.margin_left = Inches(0.18); tf.margin_top = Inches(0.14)
    tf.margin_bottom = Inches(0.14); tf.margin_right = Inches(0.18)
    tf.word_wrap = True
    if title:
        p = tf.paragraphs[0]
        set_run(p.add_run(), title, size=size + 2, bold=True, color=accent)
        p2 = tf.add_paragraph(); p2.space_before = Pt(6)
        set_run(p2.add_run(), text, size=size, color=TEXT)
    else:
        p = tf.paragraphs[0]
        set_run(p.add_run(), text, size=size, color=TEXT)
    return box


def add_section_header(slide, left, top, width, text, *, color=NAVY, size=17):
    box = add_textbox(slide, left, top, width, Inches(0.45))
    tf = box.text_frame; tf.margin_left = 0; tf.margin_top = 0
    p = tf.paragraphs[0]
    set_run(p.add_run(), text, size=size, bold=True, color=color)
    add_rect(slide, left, top + Inches(0.42), width, Inches(0.03), fill=color)


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_table(slide, left, top, headers, rows, *,
              col_widths, hdr_h=0.50, row_h=0.50,
              hdr_size=13, body_size=12, header_fill=NAVY):
    cur = left
    for w, h in zip(col_widths, headers):
        add_rect(slide, cur, top, Inches(w), Inches(hdr_h), fill=header_fill)
        b = add_textbox(slide, cur, top, Inches(w), Inches(hdr_h))
        tf = b.text_frame; tf.margin_left = Inches(0.12); tf.margin_top = Inches(0.10)
        p = tf.paragraphs[0]
        set_run(p.add_run(), h, size=hdr_size, bold=True, color=WHITE)
        cur += Inches(w)
    for ri, row in enumerate(rows):
        y = top + Inches(hdr_h + ri * row_h)
        cur = left
        fill = LIGHT if ri % 2 == 0 else WHITE
        total_w = sum(col_widths)
        add_rect(slide, left, y, Inches(total_w), Inches(row_h), fill=fill)
        for ci, (w, val) in enumerate(zip(col_widths, row)):
            b = add_textbox(slide, cur, y, Inches(w), Inches(row_h))
            tf = b.text_frame; tf.margin_left = Inches(0.12); tf.margin_top = Inches(0.08)
            tf.word_wrap = True
            p = tf.paragraphs[0]
            bold = ci == 0
            set_run(p.add_run(), val, size=body_size, bold=bold,
                    color=NAVY if bold else TEXT)
            cur += Inches(w)


# ======================================================================
prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H

TOTAL = 25


# ============ 1. Title ============
s = blank_slide(prs)
add_rect(s, Inches(0), Inches(0), SLIDE_W, SLIDE_H, fill=NAVY)
add_rect(s, Inches(0), Inches(2.95), SLIDE_W, Inches(0.06), fill=TEAL)

t = s.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(12), Inches(1.3))
tf = t.text_frame; tf.margin_left = 0
p = tf.paragraphs[0]
set_run(p.add_run(), "Med Assist", size=64, bold=True, color=WHITE)

sub = s.shapes.add_textbox(Inches(0.7), Inches(2.45), Inches(12), Inches(0.7))
tf = sub.text_frame; tf.margin_left = 0
p = tf.paragraphs[0]
set_run(p.add_run(),
        "An AI-Enhanced Consultation Tool for Online Doctor–Patient Meetings",
        size=22, color=RGBColor(0xCF, 0xDB, 0xE8))

a = s.shapes.add_textbox(Inches(0.7), Inches(3.4), Inches(12), Inches(2.5))
tf = a.text_frame; tf.margin_left = 0
p = tf.paragraphs[0]
set_run(p.add_run(), "Essam Sheikh   ", size=24, bold=True, color=WHITE)
set_run(p.add_run(), "(2595328)", size=22, color=RGBColor(0xCF, 0xDB, 0xE8))
p2 = tf.add_paragraph(); p2.space_before = Pt(10)
set_run(p2.add_run(), "Supervisor: Mohammed Bahja", size=18,
        color=RGBColor(0xCF, 0xDB, 0xE8))
p3 = tf.add_paragraph(); p3.space_before = Pt(6)
set_run(p3.add_run(),
        "BSc Computer Science Final Year Project  ·  University of Birmingham",
        size=16, color=RGBColor(0xCF, 0xDB, 0xE8))

f = s.shapes.add_textbox(Inches(0.7), Inches(6.85), Inches(12), Inches(0.4))
tf = f.text_frame; tf.margin_left = 0
p = tf.paragraphs[0]
set_run(p.add_run(), "Final Inspection — Project Demonstration",
        size=14, color=RGBColor(0x9A, 0xB0, 0xC4))


# ============ 2. The Problem ============
s = blank_slide(prs)
add_title_bar(s, "The Problem",
              "Why an AI consultation assistant is worth building")
add_footer(s, 2, TOTAL)

add_bullets(s, Inches(0.55), Inches(1.30), Inches(12.3), Inches(3.0), [
    ("Doctors are doing three things at once.",
     "Listening to the patient, reasoning clinically, and knowing they will need to write it all up afterwards. "
     "Splitting attention this way causes details to be missed."),
    ("The note-taking comes at a cost.",
     "Documentation is rewritten after the call. That slows the practice down and adds risk that something important "
     "gets left out."),
    ("Reviewing returning patients is slow.",
     "Doctors currently sift through past notes by hand. There is a real efficiency win in being able to ask a "
     "natural-language question instead."),
], size=16, label_size=17, gap=14)

add_callout(s, Inches(0.55), Inches(4.65), Inches(12.3), Inches(2.20),
    "Patient information is regulated under UK-GDPR and NHS Information Governance, so sending audio or transcripts "
    "to a third-party server is not acceptable in primary care. That single rule is what shaped every architectural "
    "choice in this project: every component — the meeting bot, the speech-to-text, the language model, and the "
    "search index — has to run on the doctor's own laptop.",
    accent=ACCENT, fill=RED_BG,
    title="The constraint that shapes everything: keep all patient data local",
    size=14)


# ============ 3. Competitor Landscape ============
s = blank_slide(prs)
add_title_bar(s, "What's Already Out There",
              "And why none of it fits an NHS GP setting")
add_footer(s, 3, TOTAL)

headers = ["Product", "What it does", "Why it doesn't fit"]
rows = [
    ("Otter.ai / Fireflies.ai",
     "Generic meeting transcription with AI summaries.",
     "Audio is processed in their cloud, mostly US-hosted."),
    ("Recall.ai",
     "Developer API that joins meetings as a bot and returns a transcript.",
     "All audio still passes through their servers — I tried this and rejected it."),
    ("Nuance DAX Copilot",
     "Mature ambient clinical scribe used in some hospitals.",
     "Cloud-dependent and priced for whole-trust procurement, not GPs."),
    ("Microsoft Dragon Medical",
     "Clinical speech recognition widely used inside NHS trusts.",
     "Trust-level deployment; individual practices don't control the infrastructure."),
    ("Med Assist  (this project)",
     "Bot, transcription, insights, weekly review and patient Q&A — all five.",
     "Self-hosted on the clinician's own laptop. Designed for the constraint."),
]
add_table(s, Inches(0.55), Inches(1.30),
          headers, rows,
          col_widths=[3.0, 5.4, 4.8],
          hdr_h=0.55, row_h=0.92, hdr_size=14, body_size=13)


# ============ 4. My Solution — Five Core Components ============
s = blank_slide(prs)
add_title_bar(s, "My Solution  —  Five Core Components",
              "A web application that covers the whole consultation lifecycle")
add_footer(s, 4, TOTAL)

modules = [
    ("1.  Meeting Bot and Transcription",
     TEAL,
     "A self-hosted Vexa.ai bot joins the Google Meet through a headless Playwright-driven Chromium browser, "
     "captures all audio, and transcribes it locally with Faster-Whisper. The result is a speaker-labelled "
     "transcript stored in SQLite."),
    ("2.  Manual AI Insights",
     NAVY2,
     "After the call, an LLM reads the transcript, the patient's record, and relevant NICE guidelines fetched "
     "via FAISS using RAG. It returns a structured JSON problem list for the doctor to view."),
    ("3.  Live AI Insights",
     ACCENT,
     "During the call, a background worker runs every 12 seconds, processes only the newest transcript lines, "
     "and pushes a JSON update to a Chrome extension panel — giving the doctor in-meeting prompts about emerging "
     "problems, risks, and follow-up questions."),
    ("4.  AI Analytics",
     GOLD,
     "At the end of each week the system reads the key points already generated by Manual Insights for each "
     "consultation and summarises the caseload — without ever touching the raw transcripts again."),
    ("5.  Ask AI Chatbot",
     GREEN,
     "A LangGraph ReAct agent lets the doctor ask free-text questions about any patient. It searches that "
     "patient's raw transcripts through FAISS and answers only from what is actually there."),
]
y = 1.30
for label, color, body in modules:
    add_rect(s, Inches(0.55), Inches(y), Inches(0.10), Inches(1.05), fill=color)
    box = add_textbox(s, Inches(0.70), Inches(y), Inches(12.2), Inches(1.05), fill=LIGHT)
    tf = box.text_frame
    tf.margin_left = Inches(0.20); tf.margin_top = Inches(0.10); tf.margin_right = Inches(0.20)
    tf.word_wrap = True
    p = tf.paragraphs[0]
    set_run(p.add_run(), label, size=15, bold=True, color=color)
    p2 = tf.add_paragraph(); p2.space_before = Pt(4)
    set_run(p2.add_run(), body, size=13, color=TEXT)
    y += 1.10


# ============ 5. How a Doctor Uses Med Assist ============
s = blank_slide(prs)
add_title_bar(s, "How a Doctor Uses Med Assist",
              "From signing in to ending the day's clinic")
add_footer(s, 5, TOTAL)

add_bullets(s, Inches(0.55), Inches(1.30), Inches(7.6), Inches(5.5), [
    ("Sign in.",
     "The doctor logs into the React web app with their email and password."),
    ("Land on the dashboard.",
     "Recently-viewed patients, recent consultations, and a clear button to start a new one."),
    ("Add or pick a patient.",
     "Patient Records page lists every patient with their ID, gender and DOB. New patients can be added here."),
    ("Start a consultation.",
     "Paste the Google Meet URL — the backend tells the Vexa bot to join and the transcript starts filling in live."),
    ("During the call.",
     "Live AI Insights stream into the Chrome extension panel sitting next to Google Meet."),
    ("After the call.",
     "Press Generate to produce the post-call summary. The transcript and insights are saved to the consultation page."),
    ("End of the week.",
     "The AI Analytics page shows a narrative summary of the week's caseload."),
    ("Ask AI.",
     "At any point, the doctor can ask free-text questions about any patient and get a grounded answer."),
], size=14, label_size=15, gap=10)

add_image_placeholder(s, Inches(8.35), Inches(1.30), Inches(4.6), Inches(5.55),
    "Doctor dashboard — recent consultations, patients, 'New consultation' CTA")


# ============ 6. System Architecture ============
s = blank_slide(prs)
add_title_bar(s, "System Architecture",
              "Everything talks to itself over localhost — nothing leaves the machine")
add_footer(s, 6, TOTAL)

add_image_placeholder(s, Inches(0.55), Inches(1.30), Inches(8.0), Inches(5.55),
    "Architecture diagram from the report  (Figure 1)", accent=TEAL)

add_section_header(s, Inches(8.85), Inches(1.30), Inches(4.10),
                   "How it fits together", size=17)
add_bullets(s, Inches(8.85), Inches(1.85), Inches(4.10), Inches(5.0), [
    ("Client.",
     "A React web app and a small Chrome extension that share the same login."),
    ("Capture.",
     "A Vexa bot in Docker joins the call, transcribes the audio with Whisper."),
    ("Backend.",
     "FastAPI runs the API and triggers the AI work in the background."),
    ("Storage.",
     "SQLite for everything; FAISS for two search indexes."),
    ("AI.",
     "Llama runs locally through Ollama. Only one outbound link: Google Meet itself."),
], size=13.5, label_size=14.5, gap=10)


# ============ 7. Tech Stack ============
s = blank_slide(prs)
add_title_bar(s, "Technology Stack",
              "Each choice driven by 'must run on a single laptop without sending data out'")
add_footer(s, 7, TOTAL)

headers = ["Layer", "Technology", "Why this one"]
rows = [
    ("Backend API",   "FastAPI (Python)",                 "Async; background tasks for slow LLM calls"),
    ("Database",      "SQLite + SQLAlchemy (WAL mode)",   "Zero setup; allows concurrent writes"),
    ("Frontend",      "React + Vite",                     "Fast iteration with hot reload"),
    ("Extension",     "Chrome Manifest V3 side panel",     "Sits next to Google Meet; shares the web app login"),
    ("Meeting bot",   "Vexa.ai (Docker Compose)",          "Open-source, self-hosted, supports Google Meet"),
    ("Transcription", "Faster-Whisper (small)",            "Largest Whisper model that runs in real time on CPU"),
    ("LLM (insights)","Ollama + Llama 3.2 (3B)",          "Fits in 16 GB RAM; ~10 s per call on CPU"),
    ("LLM (Ask AI)",  "Ollama + Llama 3.1 (8B)",          "8B is properly trained for tool-calling"),
    ("Embeddings",    "all-MiniLM-L6-v2",                  "Runs on CPU; no external calls"),
    ("Search index",  "FAISS",                             "In-memory vector search, no extra service"),
    ("Agent",         "LangChain + LangGraph",             "Standard reasoning-and-tool-use loop"),
]
add_table(s, Inches(0.55), Inches(1.30),
          headers, rows,
          col_widths=[3.0, 4.2, 6.0],
          hdr_h=0.50, row_h=0.47, hdr_size=13, body_size=12)


# ============ 8. Database Schema ============
s = blank_slide(prs)
add_title_bar(s, "Database Schema",
              "Three groups of tables — what each one stores and why")
add_footer(s, 8, TOTAL)

cols = [
    ("People & meetings", TEAL, [
        ("User", "the doctor's account, with their specialty so AI prompts match their domain."),
        ("Patient", "name, date of birth, and a short medical history that's sent into every AI call."),
        ("Consultation", "links a patient to a doctor; tracks whether the call is in progress or finished."),
    ]),
    ("Speech & insight", NAVY, [
        ("TranscriptEntry", "every spoken line, with who said it and when."),
        ("AIInsight", "the post-call summary — one row per consultation."),
        ("LiveInsight", "the in-call updates — one row each time the live worker runs."),
    ]),
    ("Chat & weekly review", ACCENT, [
        ("ChatSession / ChatMessage", "the conversations the doctor has with Ask AI."),
        ("AIAnalytics", "the weekly summary, cached so it doesn't have to be regenerated on every page load."),
    ]),
]

x0 = 0.55; col_w = 4.10; gap = 0.10
for i, (title, color, items) in enumerate(cols):
    cx = Inches(x0 + i * (col_w + gap))
    add_rect(s, cx, Inches(1.30), Inches(col_w), Inches(0.55), fill=color)
    box = add_textbox(s, cx, Inches(1.30), Inches(col_w), Inches(0.55))
    tf = box.text_frame; tf.margin_left = Inches(0.18); tf.margin_top = Inches(0.10)
    p = tf.paragraphs[0]
    set_run(p.add_run(), title, size=15, bold=True, color=WHITE)

    body = add_textbox(s, cx, Inches(1.90), Inches(col_w), Inches(4.7), fill=LIGHT)
    tf = body.text_frame
    tf.margin_left = Inches(0.20); tf.margin_right = Inches(0.18); tf.margin_top = Inches(0.20)
    tf.word_wrap = True
    for j, (label, desc) in enumerate(items):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.space_before = Pt(0 if j == 0 else 12)
        set_run(p.add_run(), label, size=14, bold=True, color=NAVY)
        p2 = tf.add_paragraph(); p2.space_before = Pt(2)
        set_run(p2.add_run(), desc, size=12.5, color=TEXT)

add_callout(s, Inches(0.55), Inches(6.75), Inches(12.3), Inches(0.5),
    "WAL mode matters: it lets the bot write transcripts at the same time the live AI worker is writing insights, "
    "without one blocking the other.",
    accent=ACCENT, size=12)


# ============ 9. Audio Capture Journey ============
s = blank_slide(prs)
add_title_bar(s, "How I Got the Audio  —  Three Attempts",
              "Each one taught me something the next one had to fix")
add_footer(s, 9, TOTAL)

phases = [
    ("Attempt 1", "Custom Chrome Extension", ACCENT,
     "I built my own Chrome extension that grabbed two audio streams (one per speaker) and sent them to "
     "OpenAI's Whisper API for transcription.",
     "Browser audio APIs are restrictive, the two streams drifted out of sync, and — fatally — the audio "
     "was leaving the laptop for OpenAI's servers."),
    ("Attempt 2", "Recall.ai (cloud bot)", GOLD,
     "Recall.ai is a service where you give it a meeting link and it sends a bot in. The transcripts came back "
     "neatly with proper speaker labels.",
     "Worked really well technically, but the audio still went through Recall's cloud. After speaking with my "
     "supervisor, the rule became 'nothing cloud-touching at all.'"),
    ("Attempt 3", "Self-hosted Vexa.ai", TEAL,
     "Vexa is an open-source project that runs the same kind of bot, but on your own machine, in Docker. It uses "
     "Faster-Whisper running on CPU.",
     "This is what I shipped. The bot only listens — it never speaks into the call — and nothing about the audio "
     "or transcript ever leaves the laptop."),
]

x0 = 0.55; card_w = 4.10; gap = 0.10
for i, (tag, name, color, what, why) in enumerate(phases):
    cx = Inches(x0 + i * (card_w + gap))
    add_rect(s, cx, Inches(1.30), Inches(card_w), Inches(0.65), fill=color)
    box = add_textbox(s, cx, Inches(1.30), Inches(card_w), Inches(0.65))
    tf = box.text_frame; tf.margin_left = Inches(0.20); tf.margin_top = Inches(0.13)
    p = tf.paragraphs[0]
    set_run(p.add_run(), f"{tag}  ·  ", size=13, bold=True, color=WHITE)
    set_run(p.add_run(), name, size=15, bold=True, color=WHITE)

    body = add_textbox(s, cx, Inches(2.00), Inches(card_w), Inches(4.85), fill=LIGHT)
    tf = body.text_frame
    tf.margin_left = Inches(0.22); tf.margin_right = Inches(0.20); tf.margin_top = Inches(0.20)
    tf.word_wrap = True
    p = tf.paragraphs[0]
    set_run(p.add_run(), "What I did:  ", size=13, bold=True, color=NAVY)
    p2 = tf.add_paragraph(); p2.space_before = Pt(2)
    set_run(p2.add_run(), what, size=13, color=TEXT)
    p3 = tf.add_paragraph(); p3.space_before = Pt(12)
    set_run(p3.add_run(), "Why I changed:  ", size=13, bold=True, color=ACCENT)
    p4 = tf.add_paragraph(); p4.space_before = Pt(2)
    set_run(p4.add_run(), why, size=13, color=TEXT)


# ============ 10. Vexa Integration ============
s = blank_slide(prs)
add_title_bar(s, "How Vexa Plugs into the App",
              "Plus the trickiest engineering problem I ran into")
add_footer(s, 10, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.0),
                   "What my backend does", size=17)
add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.0), Inches(2.6), [
    ("When a consultation starts,",
     "the backend pulls the meeting ID out of the link and asks Vexa to send its bot in (listen-only)."),
    ("While the call is on,",
     "it polls Vexa for the latest transcript and writes new lines to the database, "
     "labelling who is the doctor and who is the patient."),
    ("When the consultation ends,",
     "it tells Vexa to remove the bot from the call."),
], size=14, label_size=15, gap=12)

add_section_header(s, Inches(7.00), Inches(1.30), Inches(5.95),
                   "The synchronisation problem", size=17)
add_callout(s, Inches(7.00), Inches(1.85), Inches(5.95), Inches(2.10),
    "Whisper keeps revising what it just transcribed as more audio comes in. If I naively replaced the whole "
    "transcript on every poll, confirmed earlier lines would flicker and the live AI would think they were new.",
    accent=ACCENT, fill=RED_BG, title="What was going wrong", size=13)
add_callout(s, Inches(7.00), Inches(4.10), Inches(5.95), Inches(2.20),
    "On every sync I remember when each line was first seen. New lines get a new timestamp, but lines that were "
    "already there keep theirs. So earlier transcripts stay stable and only the still-evolving tail is allowed "
    "to change.",
    accent=GREEN, fill=GREEN_BG, title="The fix", size=13)

add_callout(s, Inches(0.55), Inches(4.70), Inches(6.00), Inches(2.15),
    "The transcript writer and the live AI worker both write to the same SQLite file. The live worker commits and "
    "lets go of its lock before making the slow LLM call, so they never block each other.",
    accent=NAVY, title="Why both can write at once", size=13)


# ============ 11. NICE Guidelines & RAG ============
s = blank_slide(prs)
add_title_bar(s, "NICE Guidelines  —  Why and How",
              "Where the AI gets its clinical knowledge, and how I keep it grounded")
add_footer(s, 11, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.0),
                   "Why I added NICE retrieval", size=17, color=ACCENT)
add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.0), Inches(5.0), [
    ("Stops the AI making things up.",
     "Without NICE, the model has to lean on its own training data for clinical advice — which is exactly the "
     "kind of generic, unverified medical opinion I want to avoid."),
    ("NICE is the standard reference in the UK.",
     "If the AI is going to surface clinical considerations to a GP, they need to come from an authoritative source, "
     "not the model's imagination."),
    ("Provenance is preserved.",
     "The prompt explicitly separates 'this came from the transcript' from 'this came from a guideline', so the "
     "doctor can tell which is which."),
    ("Pairs with the anti-inference rule.",
     "Together they push the model from 'creative clinician' to 'literal scribe with a reference book'."),
], size=14, label_size=15, gap=12)

add_section_header(s, Inches(7.00), Inches(1.30), Inches(5.95),
                   "How I built the corpus", size=17)
add_bullets(s, Inches(7.00), Inches(1.85), Inches(5.95), Inches(5.0), [
    ("Picked four guidelines by hand from nice.org.uk.",
     "Patient experience, chest pain, respiratory infection prescribing, and shared decision-making."),
    ("Manually chunked into plain text files.",
     "I copied the operative recommendation sections only — no preamble, no committee references."),
    ("Indexed offline.",
     "RecursiveCharacterTextSplitter (chunk_size=800, chunk_overlap=150) → all-MiniLM-L6-v2 embeddings → "
     "FAISS index saved to disk."),
    ("Loaded once at runtime.",
     "The KnowledgeBase service loads the FAISS index lazily on first query and re-uses it for the rest of the session."),
], size=14, label_size=15, gap=12)


# ============ 12. Manual AI Insights — Pipeline ============
s = blank_slide(prs)
add_title_bar(s, "Manual AI Insights  —  The Pipeline",
              "What runs when the doctor presses 'Generate' after the call")
add_footer(s, 12, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.4),
                   "What goes into the prompt", size=17)
add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.4), Inches(5.0), [
    ("Patient record.",
     "Name, date of birth, gender, and the key_history string — the EHR background."),
    ("Full transcript.",
     "Every TranscriptEntry sorted by timestamp and formatted as '[speaker]: text'. Capped at 8000 characters "
     "from the tail to prioritise recent dialogue."),
    ("Top-3 NICE chunks via RAG.",
     "Retrieved from the persisted FAISS index using 'consultation.about + first 600 chars of transcript' as the query — "
     "scoped to the visit reason, not the whole patient history."),
    ("Sectioned with explicit labels.",
     "The prompt clearly marks each section ('--- PATIENT RECORD ---', '--- NICE GUIDELINES ---') so the model "
     "knows which is which."),
], size=13.5, label_size=14.5, gap=12)

add_section_header(s, Inches(7.30), Inches(1.30), Inches(5.65),
                   "Model and configuration", size=17)
add_bullets(s, Inches(7.30), Inches(1.85), Inches(5.65), Inches(3.5), [
    ("Model.",  "Llama 3.2 (3B), served by Ollama."),
    ("temperature = 0.0.",  "Deterministic — same input gives the same output."),
    ("num_ctx = 6000.",  "Big enough for the full transcript and the NICE chunks."),
    ("num_predict = 700.",  "Room for a thorough four-section JSON response."),
    ("repeat_penalty = 1.2.",  "Stops the model looping when transcripts get long."),
    ("keep_alive = -1.",  "Model stays in RAM permanently — avoids the cold-start delay."),
], size=13.5, label_size=14.5, gap=8)

add_callout(s, Inches(7.30), Inches(5.55), Inches(5.65), Inches(1.30),
    "Output is a JSON object with four fields: summary, key_points, suggested_questions, risk_flags. Saved to one "
    "ai_insights row per consultation.",
    accent=NAVY, size=13, title="Output")


# ============ 13. Manual AI Insights — Bugs & Fixes ============
s = blank_slide(prs)
add_title_bar(s, "Manual AI Insights  —  Bugs and Fixes",
              "What broke during development — and how the prompt evolved")
add_footer(s, 13, TOTAL)

bugs = [
    ("Hallucinated comorbidities",
     "The model would assume things — a diabetic patient was given hypertension despite no transcript evidence.",
     "Strict grounding rule added: 'Never infer, imply or assume medical diagnoses. If a condition is not "
     "explicitly spoken in the transcript, it does not exist.'",
     ACCENT),
    ("Prompt examples leaking into output",
     "Earlier versions of my prompt had illustrative symptoms like 'exertional chest pain'. The 3B model copied "
     "them word-for-word into unrelated patients.",
     "Stripped every medical example out of the prompt. The model now only repeats text from the actual transcript.",
     GOLD),
    ("JSON parse errors",
     "Model wrapped its output in ```json fences, breaking my json.loads call.",
     "Hard rule in the prompt: 'Return ONLY a valid JSON object. No markdown, no explanation.' Plus a code-level "
     "sanitiser that strips any stray fences before parsing.",
     TEAL),
    ("NICE search pulled wrong guidelines",
     "A patient with acute UTI but a background of knee arthritis got chronic-pain guidelines applied to their UTI.",
     "Scoped the retrieval query to consultation.about plus the first 600 chars of the transcript — the acute "
     "complaint, not the whole chart.",
     NAVY),
    ("Edge case still open: medication leak",
     "When a patient came specifically to discuss medication adjustment, the model mentioned the drug despite a "
     "'Do NOT mention medications' formatting rule.",
     "Accepted as a safe failure — omitting the drug would have made the summary factually incomplete. "
     "Documented as a known 3B-model limitation.",
     MUTED),
]

y = 1.20
for title, what, fix, color in bugs:
    add_rect(s, Inches(0.55), Inches(y), Inches(0.10), Inches(1.10), fill=color)
    box = add_textbox(s, Inches(0.70), Inches(y), Inches(12.2), Inches(1.10), fill=LIGHT)
    tf = box.text_frame
    tf.margin_left = Inches(0.20); tf.margin_top = Inches(0.10); tf.margin_right = Inches(0.20)
    tf.word_wrap = True
    p = tf.paragraphs[0]
    set_run(p.add_run(), title, size=14, bold=True, color=color)
    p2 = tf.add_paragraph(); p2.space_before = Pt(2)
    set_run(p2.add_run(), "What happened: ", size=12.5, bold=True, color=NAVY)
    set_run(p2.add_run(), what, size=12.5, color=TEXT)
    p3 = tf.add_paragraph(); p3.space_before = Pt(2)
    set_run(p3.add_run(), "Fix: ", size=12.5, bold=True, color=GREEN)
    set_run(p3.add_run(), fix, size=12.5, color=TEXT)
    y += 1.16


# ============ 14. Manual Insights — Screenshot ============
s = blank_slide(prs)
add_title_bar(s, "Manual AI Insights  —  In Practice",
              "What the doctor sees on the consultation page")
add_footer(s, 14, TOTAL)
add_image_placeholder(s, Inches(0.55), Inches(1.25), Inches(12.3), Inches(5.65),
    "Consultation detail view — transcript on the left, AI Insights panel on the right "
    "(Summary, Key Points, Suggested Questions, Risk Flags)", accent=TEAL)


# ============ 15. Live AI Insights — Pipeline ============
s = blank_slide(prs)
add_title_bar(s, "Live AI Insights  —  The Pipeline",
              "Differential processing keeps the prompt size constant as the consultation grows")
add_footer(s, 15, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.4),
                   "What goes into the prompt", size=17)
add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.4), Inches(5.0), [
    ("Trigger.",
     "FastAPI BackgroundTask fires every 12 seconds while the consultation is in progress."),
    ("New transcript delta.",
     "Only the TranscriptEntry rows created after the last LiveInsight timestamp — not the whole transcript."),
    ("Established facts list.",
     "All previous LiveInsight records flattened into a de-duplicated bullet list, so the model knows what's "
     "already been reported and won't repeat itself."),
    ("Bridge context.",
     "Just the last 800 characters of the full transcript — enough for coherence, far cheaper than the whole thing."),
    ("No NICE retrieval here.",
     "FAISS plus the extra prompt tokens push past the 12-second budget on CPU. Guideline awareness lives "
     "in Manual Insights only."),
], size=13.5, label_size=14.5, gap=10)

add_section_header(s, Inches(7.30), Inches(1.30), Inches(5.65),
                   "Model and configuration", size=17)
add_bullets(s, Inches(7.30), Inches(1.85), Inches(5.65), Inches(3.5), [
    ("Model.",  "Llama 3.2 (3B), same model as Manual Insights."),
    ("temperature = 0.0.",  "Deterministic on the same delta."),
    ("num_ctx = 2048.",  "Halved from 4096 — possible because the prompt is now compact."),
    ("num_predict = 400.",  "Short JSON updates."),
    ("Output.",  "summary, new_problems, suggestions, risks_context. If all four come back empty, nothing is saved."),
], size=13.5, label_size=14.5, gap=8)

add_callout(s, Inches(7.30), Inches(5.55), Inches(5.65), Inches(1.30),
    "PROCESSING_CONSULTATIONS in-memory set stops a second worker firing while one is in flight. "
    "The session is committed and closed before the LLM call so Vexa's transcript sync can write in parallel.",
    accent=NAVY, size=12, title="Concurrency")


# ============ 16. Live AI Insights — Bugs & Fixes ============
s = blank_slide(prs)
add_title_bar(s, "Live AI Insights  —  Bugs and Fixes",
              "Average score went from below 3/10 to 7.5/10 across four targeted fixes")
add_footer(s, 16, TOTAL)

bugs = [
    ("Fix 1  —  The 120-character minimum (biggest single gain)",
     "Original code skipped any new transcript chunk shorter than 120 chars to save CPU. A 116-character family-history "
     "of melanoma was silently dropped and Risk Tracking scored 0/10.",
     "Removed the threshold entirely — the 12-second time-throttle is enough on its own. Risk Tracking jumped from "
     "0/10 to 10/10 on the next cycle.",
     ACCENT),
    ("Fix 2  —  Prompt consolidation and JSON enforcement",
     "Early prompts gave the 3B model too much structural freedom. It returned nested JSON, added markdown fences "
     "that broke the parser, and mixed new facts with already-reported ones.",
     "Hard 'JSON only, no markdown' rule plus a code-level sanitiser that strips fences before json.loads.",
     GOLD),
    ("Fix 3  —  Differential context",
     "Passing the full growing transcript every cycle made the prompt grow without bound. The model lost track "
     "of what it had already said and started repeating itself.",
     "Send only the new transcript delta + de-duplicated established-facts list + 800-char bridge. Prompt size "
     "stays constant. Let me cut num_ctx from 4096 down to 2048."),
    ("Fix 4  —  Silence preference and empty-output guard",
     "Without instruction the model documented small talk as clinical output. In one test it logged a "
     "'broken-down car' as a clinical problem.",
     "Added 'silence is better than repetition' to the prompt, and skip the database write entirely when all "
     "four output fields come back empty.",
     NAVY),
]

y = 1.25
for entry in bugs:
    if len(entry) == 4:
        title, what, fix, color = entry
    else:
        title, what, fix = entry; color = TEAL
    add_rect(s, Inches(0.55), Inches(y), Inches(0.10), Inches(1.36), fill=color)
    box = add_textbox(s, Inches(0.70), Inches(y), Inches(12.2), Inches(1.36), fill=LIGHT)
    tf = box.text_frame
    tf.margin_left = Inches(0.20); tf.margin_top = Inches(0.12); tf.margin_right = Inches(0.20)
    tf.word_wrap = True
    p = tf.paragraphs[0]
    set_run(p.add_run(), title, size=14, bold=True, color=color)
    p2 = tf.add_paragraph(); p2.space_before = Pt(3)
    set_run(p2.add_run(), "What happened: ", size=13, bold=True, color=NAVY)
    set_run(p2.add_run(), what, size=13, color=TEXT)
    p3 = tf.add_paragraph(); p3.space_before = Pt(2)
    set_run(p3.add_run(), "Fix: ", size=13, bold=True, color=GREEN)
    set_run(p3.add_run(), fix, size=13, color=TEXT)
    y += 1.42


# ============ 17. Live Insights / Chrome Extension — Screenshot ============
s = blank_slide(prs)
add_title_bar(s, "Live AI Insights  —  In Practice",
              "How insights appear in the Chrome extension during a live consultation")
add_footer(s, 17, TOTAL)
add_image_placeholder(s, Inches(0.55), Inches(1.25), Inches(8.0), Inches(5.65),
    "Chrome extension side panel during an active consultation — Summary, Problems, "
    "Suggestions, Risks cards prepended as new insights arrive", accent=ACCENT)
add_bullets(s, Inches(8.85), Inches(1.30), Inches(4.10), Inches(5.55), [
    ("Cookie-shared login.",
     "No second login — the extension reads the cookie set by the React app."),
    ("Polling cadence.",
     "Every 8 s for an active consultation, then every 5 s for new insights."),
    ("Render order.",
     "Most recent at the top, expandable cards for each section."),
    ("Race-condition fix.",
     "clearInsightsState() runs on consultation end and on URL change, so insights "
     "from one call don't bleed into the next."),
], size=13, label_size=14, gap=10)


# ============ 18. Weekly AI Analytics — Pipeline + Fixes ============
s = blank_slide(prs)
add_title_bar(s, "Weekly AI Analytics",
              "Reads the post-call notes for the week — never re-reads the raw transcripts")
add_footer(s, 18, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.25), Inches(6.4),
                   "How the pipeline works", size=17)
add_bullets(s, Inches(0.55), Inches(1.80), Inches(6.4), Inches(5.0), [
    ("Find the week.",
     "The endpoint takes a target_date and calculates the ISO-week Monday."),
    ("Pull the consultations.",
     "Every consultation for the logged-in doctor in that 7-day window with status='completed'."),
    ("Read key_points only.",
     "Concatenated into a LangChain prompt — the raw transcripts are never touched here."),
    ("Inject exact counts as variables.",
     "consultation_count and patient_count go in as numeric variables so the LLM can't make them up."),
    ("Model.",
     "Llama 3.2 (3B), temperature = 0.3 — a touch of variation makes narrative prose more readable."),
    ("Cache the result.",
     "Saved to ai_analytics so the next page load doesn't call the LLM again."),
], size=13.5, label_size=14.5, gap=10)

add_section_header(s, Inches(7.30), Inches(1.25), Inches(5.65),
                   "Bugs found and fixed", size=17, color=ACCENT)
add_bullets(s, Inches(7.30), Inches(1.80), Inches(5.65), Inches(5.0), [
    ("Plurality bug.",
     "One patient was described as 'a large group of individuals'. Fix: inject the exact count + 'if 1, no plurals'."),
    ("Background as acute.",
     "A patient's old migraines listed as a new acute problem. Fix: explicit prompt rule separating acute "
     "complaints from background risk factors."),
    ("Healthy-patient JSON collapse.",
     "When a patient had no problems, the model produced malformed JSON. Fix: an escape hatch in the Manual "
     "Insights prompt — 'Routine Wellness Exam: No acute problems'."),
    ("NICE RAG misfire.",
     "Same root cause as in Manual Insights — fixed there by scoping the query to the visit reason."),
], size=13.5, label_size=14.5, gap=10)


# ============ 19. AI Analytics — Screenshot ============
s = blank_slide(prs)
add_title_bar(s, "AI Analytics  —  In Practice",
              "The weekly summary as the doctor sees it")
add_footer(s, 19, TOTAL)
add_image_placeholder(s, Inches(0.55), Inches(1.25), Inches(12.3), Inches(5.65),
    "Weekly AI Analytics view — patient count, consultation count, and the "
    "narrative summary across the week", accent=GOLD)


# ============ 20. Ask AI — Architecture ============
s = blank_slide(prs)
add_title_bar(s, "Ask AI  —  Architecture",
              "A LangGraph ReAct agent with one tool that searches a patient's transcripts")
add_footer(s, 20, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.4),
                   "The ReAct agent", size=17)
add_bullets(s, Inches(0.55), Inches(1.85), Inches(6.4), Inches(5.0), [
    ("Built with LangGraph create_react_agent.",
     "Standard reason-then-act loop. Decides whether to call the tool, invokes it, reads the context, writes the answer."),
    ("Single tool: get_patient_records(patient_reference, query).",
     "Defined via LangChain's @tool decorator with explicit typed arguments — so the model knows exactly what to send."),
    ("Reads raw transcripts, not AIInsight summaries.",
     "If the agent built on summaries from another model, any hallucination there would compound here. "
     "Raw transcripts are the ground truth."),
    ("Clinical guardrails.",
     "Refuses diagnosis or prescribing requests. Says 'This is not documented in the available notes' for "
     "missing facts. Crucially, does NOT over-refuse legitimate clinical lookups."),
], size=13.5, label_size=14.5, gap=10)

add_section_header(s, Inches(7.30), Inches(1.30), Inches(5.65),
                   "Inside the tool: the RAG pipeline", size=17)
add_bullets(s, Inches(7.30), Inches(1.85), Inches(5.65), Inches(5.0), [
    ("Fuzzy patient lookup.",
     "ilike match on both name and display_id, case-insensitive. So 'John' matches 'John Smith'."),
    ("Pull all transcripts.",
     "Every TranscriptEntry across every consultation for that patient."),
    ("Chunk them.",
     "RecursiveCharacterTextSplitter — chunk_size=600, chunk_overlap=100. Small overlap keeps context across chunk boundaries."),
    ("Embed locally.",
     "all-MiniLM-L6-v2 — runs on CPU, no external calls."),
    ("Top-5 FAISS similarity search.",
     "Returns the five most relevant transcript snippets. Concatenated and handed to the agent as 'Relevant Snippets'."),
], size=13.5, label_size=14.5, gap=10)


# ============ 21. Ask AI — Model Selection ============
s = blank_slide(prs)
add_title_bar(s, "Ask AI  —  Model Selection",
              "Why I switched from Llama 3.2 (3B) to Llama 3.1 (8B), and how I tuned it")
add_footer(s, 21, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.25), Inches(7.0),
                   "Why 3B failed and 8B worked", size=17)
add_bullets(s, Inches(0.55), Inches(1.80), Inches(7.0), Inches(3.6), [
    ("3B couldn't tool-call properly.",
     "Instead of a natural-language query, it sent raw JSON dicts like {\"date_of_birth\":\"date\"}. "
     "FAISS can't parse JSON, so retrieval returned nothing — and the model hallucinated answers."),
    ("8B is trained for tool-calling.",
     "Meta specifically post-trained Llama 3.1 (8B) for structured tool use. It sends queries like "
     "'demographic background' — exactly what FAISS expects."),
    ("Faithfulness jumped 0.18 → 0.75 (+317%).",
     "RAGAS evaluation, GPT-4o judge, 4 patients × 20 consultations + 3 adversarial. All 3 trick "
     "questions correctly refused."),
], size=13, label_size=14, gap=10)

# RAGAS table
hdr_y = 5.55
add_rect(s, Inches(0.55), Inches(hdr_y), Inches(2.5), Inches(0.4), fill=NAVY)
add_rect(s, Inches(3.05), Inches(hdr_y), Inches(2.0), Inches(0.4), fill=ACCENT)
add_rect(s, Inches(5.05), Inches(hdr_y), Inches(2.0), Inches(0.4), fill=GREEN)
for x, w, txt in [(0.55, 2.5, "Metric"), (3.05, 2.0, "Llama 3.2 (3B)"), (5.05, 2.0, "Llama 3.1 (8B)")]:
    box = add_textbox(s, Inches(x), Inches(hdr_y), Inches(w), Inches(0.4))
    tf = box.text_frame; tf.margin_left = Inches(0.10); tf.margin_top = Inches(0.07)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT if w > 2.0 else PP_ALIGN.CENTER
    set_run(p.add_run(), txt, size=12, bold=True, color=WHITE)

scores = [
    ("Faithfulness",      "0.18", "0.75"),
    ("Answer Relevancy",  "0.39", "0.68"),
    ("Context Precision", "0.09", "0.39"),
]
ry = hdr_y + 0.4
for i, (m, a, b) in enumerate(scores):
    y = ry + i * 0.42
    fill = LIGHT if i % 2 == 0 else WHITE
    add_rect(s, Inches(0.55), Inches(y), Inches(6.5), Inches(0.42), fill=fill)
    for x, w, txt, bold, color, align in [
        (0.55, 2.5, m, True, NAVY, PP_ALIGN.LEFT),
        (3.05, 2.0, a, False, MUTED, PP_ALIGN.CENTER),
        (5.05, 2.0, b, True, GREEN, PP_ALIGN.CENTER),
    ]:
        box = add_textbox(s, Inches(x), Inches(y), Inches(w), Inches(0.42))
        tf = box.text_frame; tf.margin_left = Inches(0.10); tf.margin_top = Inches(0.08)
        p = tf.paragraphs[0]; p.alignment = align
        set_run(p.add_run(), txt, size=12, bold=bold, color=color)

add_section_header(s, Inches(7.50), Inches(1.25), Inches(5.45),
                   "Engineering optimisations on CPU", size=17)
add_bullets(s, Inches(7.50), Inches(1.80), Inches(5.45), Inches(5.0), [
    ("Context truncation.",
     "Endpoint only injects the last 6 chat messages — beyond that, 8B latency on CPU spikes."),
    ("FAISS per-patient cache.",
     "patient_vectorstore_cache keyed by patient ID. First query builds the index; follow-ups are instant."),
    ("LLM tuning.",
     "temperature=0 (deterministic), num_predict=200 (this is a lookup tool, not a writing tool), "
     "num_ctx=4096, num_thread=8 (matches the Core Ultra 7's P-cores), keep_alive=-1."),
    ("Auto-titling.",
     "The first 30 characters of the opening message become the chat session title automatically."),
], size=13, label_size=14, gap=10)


# ============ 22. Ask AI — Screenshot ============
s = blank_slide(prs)
add_title_bar(s, "Ask AI  —  In Practice",
              "Free-text questions answered from the patient's own notes")
add_footer(s, 22, TOTAL)
add_image_placeholder(s, Inches(0.55), Inches(1.25), Inches(12.3), Inches(5.65),
    "Ask AI conversational view — patient-specific question with a bullet-pointed grounded "
    "answer and an explicit 'not documented' fallback", accent=GREEN)


# ============ 23. Evaluation ============
s = blank_slide(prs)
add_title_bar(s, "How I Tested It",
              "Three different methods — every score traces back to a code change")
add_footer(s, 23, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.25), Inches(12.3),
                   "Three methods, because each feature has different output", size=16)
add_bullets(s, Inches(0.55), Inches(1.80), Inches(12.3), Inches(2.5), [
    ("Manual Insights and Weekly Analytics:",
     "Automated scripts compare the AI's output line-by-line against the source it was given. "
     "Looks for invented facts, dropped facts, and broken formatting."),
    ("Live Insights:",
     "Custom test suite runs three scenarios (Cardiology, Dermatology, Psychiatry) and asks GPT-4o to grade "
     "the output on four dimensions. GPT-4o is independent — it doesn't know the local model."),
    ("Ask AI:",
     "RAGAS framework with GPT-4o as judge. 4 real patients, 20 consultations, plus 3 adversarial questions to "
     "verify the guardrails actually work."),
], size=14, label_size=15, gap=14)

# Score cards along the bottom
add_section_header(s, Inches(0.55), Inches(4.95), Inches(12.3), "What I got", size=16)
cards = [
    ("Manual Insights",  "7.5", TEAL),
    ("Live Insights",    "7.5", ACCENT),
    ("Weekly Analytics", "8.0", GOLD),
    ("Ask AI Faithfulness", "0.75", GREEN),
]
x = 0.55; card_w = 3.05; gap = 0.10
for i, (label, score, color) in enumerate(cards):
    cx = Inches(x + i * (card_w + gap))
    add_rect(s, cx, Inches(5.55), Inches(card_w), Inches(1.55), fill=color)
    box = add_textbox(s, cx, Inches(5.55), Inches(card_w), Inches(1.55))
    tf = box.text_frame
    tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    set_run(p.add_run(), label, size=14, bold=True, color=WHITE)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(8)
    set_run(p2.add_run(), score, size=34, bold=True, color=WHITE)
    if i == 3:
        p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER; p3.space_before = Pt(0)
        set_run(p3.add_run(), "(up from 0.18)", size=11, italic=True,
                color=RGBColor(0xCF, 0xDB, 0xE8))


# ============ 24. Limitations & Future Work ============
s = blank_slide(prs)
add_title_bar(s, "Limitations and What's Next",
              "What I know is unfinished, and what unlocks the next tier")
add_footer(s, 24, TOTAL)

add_section_header(s, Inches(0.55), Inches(1.30), Inches(6.0),
                   "Current limitations", size=18, color=ACCENT)
add_bullets(s, Inches(0.55), Inches(1.90), Inches(6.0), Inches(5.0), [
    ("Small model, hard ceiling.",
     "Llama 3.2 (3B) handles small-talk filtering and corrections imperfectly. "
     "It's a model-size issue, not a design issue."),
    ("Hardware budget.",
     "On a CPU laptop, anything bigger than 8B was either too slow or ran out of memory."),
    ("No real clinicians yet.",
     "All testing was on scripted mock consultations. No real patient data was used."),
    ("Google Meet only.",
     "The bot is configured for one platform in this version."),
], size=14.5, label_size=15.5, gap=14)

add_section_header(s, Inches(7.00), Inches(1.30), Inches(5.95),
                   "Future work", size=18, color=TEAL)
add_bullets(s, Inches(7.00), Inches(1.90), Inches(5.95), Inches(5.0), [
    ("Better LLM.",
     "GPT-4o or Claude 3.5 — projected to push the scores above 9.5/10 with no architectural change."),
    ("Better embeddings.",
     "A clinical-domain embedding model would close the remaining gap in search precision."),
    ("Clinician validation.",
     "A proper usability study with GP registrars before any clinical-utility claim."),
    ("More platforms.",
     "Microsoft Teams and Zoom support."),
], size=14.5, label_size=15.5, gap=14)


# ============ 25. Conclusion ============
s = blank_slide(prs)
add_title_bar(s, "Conclusion",
              "What I built, what I learned, what comes next")
add_footer(s, 25, TOTAL)

add_bullets(s, Inches(0.55), Inches(1.30), Inches(12.3), Inches(2.6), [
    ("Met the constraint.",
     "A five-module AI consultation assistant that runs entirely on a clinician's laptop. "
     "No patient data ever leaves the machine."),
    ("Got quantitative evidence.",
     "Manual 7.5, Live 7.5, Analytics 8.0, Ask AI faithfulness 0.18 → 0.75 after the model swap."),
    ("Three audio-capture attempts.",
     "Each rejected for a real reason — browser limits, then cloud audio, then finally the right answer."),
], size=15.5, label_size=16.5, gap=14)

add_callout(s, Inches(0.55), Inches(4.30), Inches(12.3), Inches(1.45),
    "A small model is fine for tightly-scoped, structured writing. It is not fine for multi-step tool use or for "
    "reliably following negative rules. Keeping each module narrowly scoped — and pointing it at the cleanest "
    "available data — mattered more than any individual prompt change.",
    accent=ACCENT, fill=RED_BG, title="What I learned", size=14)

q = add_textbox(s, Inches(0.55), Inches(6.05), Inches(12.3), Inches(1.0), fill=NAVY)
tf = q.text_frame
tf.margin_left = Inches(0.4); tf.margin_top = Inches(0.20)
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
set_run(p.add_run(), "Thank you  —  Questions?", size=26, bold=True, color=WHITE)


prs.save(OUT)
print(f"Saved {OUT} with {len(prs.slides)} slides")
