
import io
import random
from pathlib import Path

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# TEXTIFY AI — Text to Handwriting
# Responsive UI for phones, tablets, laptops, and desktops
# ============================================================

ROOT = Path(__file__).parent
FONT_DIR = ROOT / "assets" / "fonts"
FONT_DIR.mkdir(parents=True, exist_ok=True)

FONT_URLS = {
    "Caveat": "https://raw.githubusercontent.com/google/fonts/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
    "Patrick Hand": "https://raw.githubusercontent.com/google/fonts/main/ofl/patrickhand/PatrickHand-Regular.ttf",
    "Kalam": "https://raw.githubusercontent.com/google/fonts/main/ofl/kalam/Kalam-Regular.ttf",
}

FONT_PATHS = {
    name: FONT_DIR / (name.lower().replace(" ", "-") + ".ttf")
    for name in FONT_URLS
}

PAGE_SIZES = {
    "A4": (1240, 1754),
    "Letter": (1275, 1650),
    "A5": (874, 1240),
}

INKS = {
    "Blue": "#17458A",
    "Black": "#252525",
    "Dark green": "#24533F",
    "Purple": "#594080",
}

PAPERS = {
    "Warm white": "#FFFEF8",
    "Bright white": "#FFFFFF",
    "Cream": "#FFF8E8",
}

MAX_CHARS = 100000


# --------------------------- Font handling ---------------------------

def ensure_font(name):
    path = FONT_PATHS[name]

    if path.exists() and path.stat().st_size > 5000:
        return True

    try:
        response = requests.get(FONT_URLS[name], timeout=12)
        response.raise_for_status()

        if len(response.content) > 5000:
            path.write_bytes(response.content)
            return True
    except (requests.RequestException, OSError):
        pass

    return False


def get_font(size, name):
    path = FONT_PATHS.get(name)

    if path and path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            pass

    for fallback in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(fallback, size)
        except OSError:
            continue

    return ImageFont.load_default()


# --------------------------- Text rendering ---------------------------

def measure_text(draw, text, font, letter_spacing=0):
    if not text:
        return 0

    if letter_spacing == 0:
        return draw.textlength(text, font=font)

    return sum(
        draw.textlength(char, font=font)
        for char in text
    ) + letter_spacing * (len(text) - 1)


def draw_text(draw, position, text, font, color, letter_spacing=0):
    x, y = position

    if letter_spacing == 0:
        draw.text((x, y), text, font=font, fill=color)
        return

    for char in text:
        draw.text((x, y), char, font=font, fill=color)
        x += draw.textlength(char, font=font) + letter_spacing


def wrap_paragraph(draw, paragraph, font, max_width,
                   letter_spacing=0, extra_word_spacing=0):
    words = paragraph.split()

    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        candidate = (
            word if not current
            else current + (" " * (1 + extra_word_spacing)) + word
        )

        if measure_text(draw, candidate, font, letter_spacing) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)

        # Split a single long word if it exceeds the printable width.
        if measure_text(draw, word, font, letter_spacing) > max_width:
            part = ""

            for char in word:
                test = part + char

                if (
                    part
                    and measure_text(draw, test, font, letter_spacing)
                    > max_width
                ):
                    lines.append(part)
                    part = char
                else:
                    part = test

            current = part
        else:
            current = word

    if current:
        lines.append(current)

    return lines


def render_pages(
    text,
    page_name,
    orientation,
    paper_style,
    paper_color,
    ink,
    font_name,
    font_size,
    line_gap,
    letter_spacing,
    word_spacing,
    variation,
    margin_pct,
):
    width, height = PAGE_SIZES[page_name]

    if orientation == "Landscape":
        width, height = height, width

    left = int(width * margin_pct / 100)
    right = int(width * margin_pct / 100)
    top = int(height * margin_pct / 100) + 24
    bottom = int(height * margin_pct / 100)

    if paper_style in ("Ruled notebook", "Grid", "Margin line"):
        left += 32

    content_width = max(100, width - left - right)
    content_bottom = height - bottom

    font = get_font(font_size, font_name)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10), "white"))

    lines = []

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    for paragraph in normalized.split("\n"):
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(
                wrap_paragraph(
                    probe,
                    paragraph.rstrip(),
                    font,
                    content_width,
                    letter_spacing,
                    word_spacing,
                )
            )

    line_height = max(font_size + 4, int(line_gap))
    capacity = max(
        1,
        (height - top - bottom - 60) // line_height,
    )

    chunks = [
        lines[index:index + capacity]
        for index in range(0, len(lines), capacity)
    ] or [[]]

    pages = []
    rng = random.Random(27)

    for page_number, page_lines in enumerate(chunks, 1):
        image = Image.new("RGB", (width, height), paper_color)
        draw = ImageDraw.Draw(image)

        if paper_style == "Ruled notebook":
            for y in range(top - 8, height - bottom, line_height):
                draw.line(
                    (30, y, width - 30, y),
                    fill="#D8E6F3",
                    width=1,
                )

            draw.line(
                (left - 32, 0, left - 32, height),
                fill="#E7A3A3",
                width=2,
            )

        elif paper_style == "Grid":
            for x in range(30, width, 32):
                draw.line((x, 0, x, height), fill="#E7EDF2", width=1)

            for y in range(30, height, 32):
                draw.line((0, y, width, y), fill="#E7EDF2", width=1)

            draw.line(
                (left - 32, 0, left - 32, height),
                fill="#E7A3A3",
                width=2,
            )

        elif paper_style == "Dotted":
            for x in range(30, width, 30):
                for y in range(30, height, 30):
                    draw.ellipse(
                        (x, y, x + 2, y + 2),
                        fill="#CBD5DF",
                    )

        elif paper_style == "Margin line":
            draw.line(
                (left - 32, 55, left - 32, height - 55),
                fill="#E7A3A3",
                width=2,
            )

        y = top

        for line in page_lines:
            if not line:
                y += line_height // 2
                continue

            bbox = draw.textbbox((0, 0), line, font=font)
            actual_height = max(font_size, bbox[3] - bbox[1])

            if y + actual_height > content_bottom - 35:
                break

            x = left + (rng.randint(-3, 4) if variation else 0)
            adjusted_y = y + (rng.randint(-2, 2) if variation else 0)

            draw_text(
                draw,
                (x, adjusted_y),
                line,
                font,
                ink,
                letter_spacing,
            )

            y += line_height

        footer_font = get_font(14, "Patrick Hand")
        footer = f"Textify AI | Page {page_number}"

        draw.text(
            (max(10, width - right - 220), height - max(28, bottom // 2)),
            footer,
            font=footer_font,
            fill="#7B8490",
        )

        pages.append(image)

    return pages


def create_pdf(pages):
    if not pages:
        raise ValueError("Generate your pages before exporting.")

    output = io.BytesIO()
    rgb_pages = [page.convert("RGB") for page in pages]

    rgb_pages[0].save(
        output,
        format="PDF",
        save_all=True,
        append_images=rgb_pages[1:],
        resolution=150,
    )

    output.seek(0)
    return output.getvalue()


# ------------------------------ Streamlit setup ------------------------------

st.set_page_config(
    page_title="Textify AI",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
    color-scheme: light;
}

.stApp {
    background: #F5F7FB;
    color: #172033;
}

.block-container {
    width: 100%;
    max-width: 1240px;
    padding: 1.5rem 1.6rem 3rem;
}

header[data-testid="stHeader"] {
    background: rgba(245,247,251,.94);
}

.hero {
    padding: 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid #DCE5F1;
    border-radius: 22px;
    background: linear-gradient(120deg,#FFFFFF,#EDF3FF);
    box-shadow: 0 8px 28px rgba(32,55,92,.05);
}

.hero-kicker {
    display: inline-block;
    padding: .35rem .7rem;
    border-radius: 999px;
    background: #E7EEFF;
    color: #3157A4;
    font-size: .75rem;
    font-weight: 750;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: .8rem;
}

.hero h1 {
    margin: 0;
    color: #15223A;
    font-size: clamp(2rem, 5vw, 3rem);
    line-height: 1.12;
    letter-spacing: -.045em;
}

.hero p {
    max-width: 680px;
    margin: .75rem 0 0;
    color: #5A6880;
    font-size: 1rem;
    line-height: 1.65;
}

.section-heading {
    color: #1A2942;
    font-size: 1.15rem;
    font-weight: 760;
    letter-spacing: -.02em;
    margin-bottom: .25rem;
}

.section-subtitle {
    color: #64748B;
    font-size: .9rem;
    line-height: 1.5;
    margin-bottom: .85rem;
}

.stApp label,
.stApp [data-testid="stWidgetLabel"] p {
    color: #27364D !important;
    font-weight: 650 !important;
    font-size: .9rem !important;
}

.stApp [data-testid="stCaptionContainer"] {
    color: #64748B !important;
    font-size: .84rem !important;
    line-height: 1.5 !important;
}

.stTextArea textarea {
    width: 100% !important;
    background: #FFFFFF !important;
    color: #172033 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 13px !important;
    line-height: 1.65 !important;
    padding: .9rem !important;
    font-size: 1rem !important;
}

.stTextArea textarea:focus {
    border-color: #6488D8 !important;
    box-shadow: 0 0 0 3px rgba(100,136,216,.15) !important;
}

.stSelectbox [data-baseweb="select"] > div {
    border-radius: 10px;
    min-height: 42px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.9);
    border: 1px solid #E0E7F0 !important;
    border-radius: 16px !important;
    padding: 1rem 1.05rem;
    box-shadow: 0 4px 18px rgba(27,48,80,.035);
}

.stButton > button,
.stDownloadButton > button {
    width: 100%;
    min-height: 44px !important;
    border-radius: 11px !important;
    font-weight: 700 !important;
    white-space: normal !important;
    transition: background .15s ease, border-color .15s ease !important;
}

.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: #315CCB !important;
    color: white !important;
    border: 1px solid #315CCB !important;
}

.stButton > button[kind="primary"] p,
.stDownloadButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stDownloadButton > button[kind="primary"] span {
    color: white !important;
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    background: #244BAF !important;
    border-color: #244BAF !important;
}

.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]) {
    background: white !important;
    color: #263750 !important;
    border: 1px solid #CBD5E1 !important;
}

.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:not([kind="primary"]):hover {
    background: #F0F5FF !important;
    border-color: #91A9D7 !important;
}

.stButton > button:focus,
.stDownloadButton > button:focus {
    outline: 2px solid #7395E1 !important;
    outline-offset: 2px !important;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E0E7F0;
    padding: .8rem;
    border-radius: 12px;
    overflow-wrap: anywhere;
}

div[data-testid="stMetricLabel"] {
    color: #64748B !important;
}

div[data-testid="stMetricValue"] {
    color: #1E3152 !important;
}

div[data-testid="stImage"] img {
    display: block;
    max-width: 100%;
    height: auto;
    border: 1px solid #E1E7EF;
    border-radius: 10px;
    box-shadow: 0 6px 18px rgba(27,48,80,.07);
}

hr {
    border-color: #E1E7F0 !important;
}

/* Tablet and phone layouts */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem .85rem 2rem;
    }

    .hero {
        padding: 1.3rem 1.15rem;
        border-radius: 17px;
        margin-bottom: 1.1rem;
    }

    .hero h1 {
        font-size: clamp(1.9rem, 8vw, 2.5rem);
    }

    .hero p {
        font-size: .94rem;
        line-height: 1.55;
    }

    .section-heading {
        font-size: 1.05rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: .85rem;
        border-radius: 13px !important;
    }

    .stTextArea textarea {
        font-size: 16px !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 46px !important;
        font-size: .95rem !important;
    }

    div[data-testid="stMetric"] {
        padding: .55rem;
    }
}

@media (max-width: 420px) {
    .block-container {
        padding-left: .65rem;
        padding-right: .65rem;
    }

    .hero {
        padding: 1.1rem .9rem;
    }

    .hero-kicker {
        font-size: .68rem;
    }

    .section-subtitle {
        font-size: .85rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        transition: none !important;
        animation: none !important;
        scroll-behavior: auto !important;
    }
}
</style>

<div class="hero">
    <div class="hero-kicker">Your text, your style</div>
    <h1>✍️ Textify AI</h1>
    <p>Turn plain text into beautiful handwritten-style pages. Customize
    your paper, ink, and typography, preview your notes, and export a PDF.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ------------------------------ Input and settings ---------------------------

if "source_text" not in st.session_state:
    st.session_state.source_text = (
        "Artificial Intelligence\n\n"
        "Artificial Intelligence (AI) is a field of computer science focused "
        "on building systems that perform tasks associated with human "
        "intelligence, such as learning, reasoning, and recognizing patterns."
        "\n\nMain areas\n"
        "• Machine Learning: systems learn patterns from data.\n"
        "• Computer Vision: systems interpret images and video.\n"
        "• Natural Language Processing: systems work with human language."
    )

left, right = st.columns([1.08, 0.92], gap="large")

with left:
    st.markdown(
        '<div class="section-heading">01 · Your content</div>'
        '<div class="section-subtitle">Paste or type the text you want '
        'to turn into handwriting.</div>',
        unsafe_allow_html=True,
    )

    source_text = st.text_area(
        "Your text",
        key="source_text",
        height=300,
        max_chars=MAX_CHARS,
        placeholder="Start typing or paste your text here...",
        label_visibility="visible",
    )

    st.caption(
        f"{len(source_text):,} characters · "
        f"{MAX_CHARS:,} character limit"
    )

with right:
    st.markdown(
        '<div class="section-heading">02 · Customize your pages</div>'
        '<div class="section-subtitle">Choose how your handwritten pages '
        'should look.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        paper_style = st.selectbox(
            "Paper style",
            ["Ruled notebook", "Plain paper", "Grid", "Dotted", "Margin line"],
        )

        paper_color = st.selectbox("Paper color", list(PAPERS.keys()))

        font_name = st.selectbox(
            "Handwriting font",
            list(FONT_URLS.keys()),
            help="If a font cannot download, a fallback font is used.",
        )

        page_name = st.selectbox("Page size", list(PAGE_SIZES.keys()))

        orientation = st.selectbox(
            "Page orientation",
            ["Portrait", "Landscape"],
        )

        font_size = st.slider("Text size", 20, 54, 34)

        line_gap = st.slider(
            "Line spacing",
            32,
            78,
            56,
            step=2,
        )

        with st.expander("Advanced typography and layout"):
            letter_spacing = st.slider("Letter spacing", -1, 4, 0)
            word_spacing = st.slider("Extra word spacing", 0, 3, 0)
            margin_pct = st.slider("Page margins", 5, 12, 8)

            variation = st.checkbox(
                "Add natural layout variation",
                value=True,
                help="Slightly varies line placement for a more natural look.",
            )

        ink_label = st.radio(
            "Ink color",
            list(INKS.keys()),
            horizontal=True,
        )
        ink = INKS[ink_label]

        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;
            padding:10px 12px;border:1px solid #DCE5F0;
            border-radius:10px;background:#F8FAFD;margin-top:5px;">
            <span style="width:18px;height:18px;border-radius:50%;
            background:{ink};border:2px solid white;
            box-shadow:0 0 0 1px #AAB6C8;flex-shrink:0"></span>
            <span style="color:#26344B">Selected ink:
            <b>{ink_label}</b></span></div>
            """,
            unsafe_allow_html=True,
        )


# ------------------------------ Generate pages ------------------------------

st.divider()

st.markdown(
    '<div class="section-heading">03 · Create your pages</div>'
    '<div class="section-subtitle">Generate a preview, then download '
    'all pages as a PDF.</div>',
    unsafe_allow_html=True,
)

generate = st.button(
    "✨ Generate handwritten pages",
    type="primary",
    use_container_width=True,
)

if generate:
    if not source_text.strip():
        st.warning("Please type or paste some text first.")
    else:
        try:
            with st.spinner("Preparing your handwritten pages..."):
                font_ready = ensure_font(font_name)

                if not font_ready:
                    st.warning(
                        f"{font_name} could not be downloaded. "
                        "A fallback font will be used."
                    )

                pages = render_pages(
                    source_text,
                    page_name,
                    orientation,
                    paper_style,
                    PAPERS[paper_color],
                    ink,
                    font_name,
                    font_size,
                    line_gap,
                    letter_spacing,
                    word_spacing,
                    variation,
                    margin_pct,
                )

                pdf_bytes = create_pdf(pages)

                st.session_state["generated_pages"] = pages
                st.session_state["generated_pdf"] = pdf_bytes
                st.session_state["generated_meta"] = {
                    "characters": len(source_text),
                    "paper": paper_style,
                    "source": source_text,
                }

            st.success(f"Your {len(pages)} page(s) are ready.")

        except Exception as error:
            st.error(f"Could not generate pages: {error}")


# ------------------------------ Preview and export ---------------------------

if "generated_pages" in st.session_state:
    pages = st.session_state["generated_pages"]
    pdf_bytes = st.session_state["generated_pdf"]
    meta = st.session_state["generated_meta"]

    st.divider()

    st.markdown(
        '<div class="section-heading">04 · Preview and export</div>'
        '<div class="section-subtitle">Check the preview before downloading '
        'your complete document.</div>',
        unsafe_allow_html=True,
    )

    metric_a, metric_b, metric_c = st.columns(3)

    metric_a.metric("Pages", len(pages))
    metric_b.metric("Characters", f"{meta['characters']:,}")
    metric_c.metric("Paper", meta["paper"])

    st.caption(
        "Showing up to three preview pages. "
        "Your PDF includes all generated pages."
    )

    preview_count = min(len(pages), 3)

    # Two columns on larger screens; Streamlit stacks columns on narrow screens.
    for start in range(0, preview_count, 2):
        preview_columns = st.columns(min(2, preview_count - start))

        for offset, column in enumerate(preview_columns):
            page_index = start + offset

            with column:
                st.image(
                    pages[page_index],
                    caption=f"Page {page_index + 1}",
                    use_container_width=True,
                )

    if len(pages) > 3:
        st.info(
            f"{len(pages) - 3} more page(s) are included in the PDF."
        )

    st.download_button(
        "⬇️ Download complete PDF",
        data=pdf_bytes,
        file_name="textify_ai_handwritten_notes.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )


# -------------------------------- Footer -------------------------------------

st.divider()

st.caption(
    "Textify AI converts text into handwriting-style page images. "
    "PDF text may not be selectable or searchable."
)
