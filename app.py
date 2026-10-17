
import io
import random
from pathlib import Path

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ---------------------------- Configuration ---------------------------------

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


def ensure_font(name):
    """Download the selected handwriting font if unavailable locally."""
    path = FONT_PATHS[name]

    if path.exists() and path.stat().st_size > 5000:
        return True

    try:
        response = requests.get(FONT_URLS[name], timeout=15)
        response.raise_for_status()

        if len(response.content) > 5000:
            path.write_bytes(response.content)
            return True

    except requests.RequestException:
        pass

    return False


def font_for(size, name):
    """Load a font, falling back to a system font if necessary."""
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


def text_width(draw, text, font, spacing=0):
    if not text:
        return 0

    if spacing == 0:
        return draw.textlength(text, font=font)

    return sum(
        draw.textlength(character, font=font)
        for character in text
    ) + spacing * (len(text) - 1)


def draw_spaced(draw, xy, text, font, fill, spacing=0):
    x, y = xy

    if spacing == 0:
        draw.text((x, y), text, font=font, fill=fill)
        return

    for character in text:
        draw.text((x, y), character, font=font, fill=fill)
        x += draw.textlength(character, font=font) + spacing


def wrap_line(
    draw,
    text,
    font,
    max_width,
    letter_spacing=0,
    extra_word_space=0,
):
    """Wrap a paragraph to fit within the page's printable width."""
    words = text.split()

    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        candidate = (
            word
            if not current
            else current + (" " * (1 + extra_word_space)) + word
        )

        if text_width(draw, candidate, font, letter_spacing) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)

            # Split unusually long words to prevent overflow.
            if text_width(draw, word, font, letter_spacing) > max_width:
                part = ""

                for character in word:
                    test = part + character

                    if (
                        part
                        and text_width(draw, test, font, letter_spacing)
                        > max_width
                    ):
                        lines.append(part)
                        part = character
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
    """Render text into customizable handwriting-style notebook pages."""
    width, height = PAGE_SIZES[page_name]

    if orientation == "Landscape":
        width, height = height, width

    margin_left = int(width * margin_pct / 100)
    margin_right = int(width * margin_pct / 100)
    margin_top = int(height * margin_pct / 100) + 24
    margin_bottom = int(height * margin_pct / 100)

    if paper_style in ("Ruled notebook", "Grid", "Margin line"):
        margin_left += 32

    content_width = max(100, width - margin_left - margin_right)
    content_bottom = height - margin_bottom

    font = font_for(font_size, font_name)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10), "white"))

    lines = []

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

    for paragraph in normalized_text.split("\n"):
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(
                wrap_line(
                    probe,
                    paragraph.rstrip(),
                    font,
                    content_width,
                    letter_spacing,
                    word_spacing,
                )
            )

    line_height = max(1, int(line_gap))
    usable_height = height - margin_top - margin_bottom - 60
    capacity = max(1, usable_height // line_height)

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
            for y in range(margin_top - 8, height - margin_bottom, line_height):
                draw.line(
                    (30, y, width - 30, y),
                    fill="#D8E6F3",
                    width=1,
                )

            draw.line(
                (margin_left - 32, 0, margin_left - 32, height),
                fill="#E7A3A3",
                width=2,
            )

        elif paper_style == "Grid":
            for x in range(30, width, 32):
                draw.line(
                    (x, 0, x, height),
                    fill="#E7EDF2",
                    width=1,
                )

            for y in range(30, height, 32):
                draw.line(
                    (0, y, width, y),
                    fill="#E7EDF2",
                    width=1,
                )

            draw.line(
                (margin_left - 32, 0, margin_left - 32, height),
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
                (margin_left - 32, 55, margin_left - 32, height - 55),
                fill="#E7A3A3",
                width=2,
            )

        y = margin_top

        for line in page_lines:
            if not line:
                y += line_height // 2
                continue

            bbox = draw.textbbox((0, 0), line, font=font)
            actual_height = max(font_size, bbox[3] - bbox[1])

            if y + actual_height > content_bottom - 35:
                break

            x = margin_left + (rng.randint(-3, 4) if variation else 0)
            adjusted_y = y + (rng.randint(-2, 2) if variation else 0)

            draw_spaced(
                draw,
                (x, adjusted_y),
                line,
                font,
                ink,
                letter_spacing,
            )

            y += line_height

        footer_font = font_for(14, "Patrick Hand")
        footer_label = f"Textify AI • Page {page_number}"

        draw.text(
            (
                width - margin_right - 220,
                height - max(28, margin_bottom // 2),
            ),
            footer_label,
            font=footer_font,
            fill="#7B8490",
        )

        pages.append(image)

    return pages


def to_pdf(pages):
    """Convert rendered pages into a multi-page PDF."""
    if not pages:
        raise ValueError("No pages to export.")

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


# ---------------------------- Page configuration ----------------------------

st.set_page_config(
    page_title="Textify AI",
    page_icon="✍️",
    layout="wide",
)

st.markdown(
    """
<style>
:root { color-scheme: light; }

.stApp {
    background: #F5F7FB;
    color: #172033;
}

.block-container {
    max-width: 1320px;
    padding: 1.7rem 2rem 3.5rem;
}

header[data-testid="stHeader"] {
    background: rgba(245,247,251,.92);
}

.hero {
    position: relative;
    overflow: hidden;
    padding: 2rem 2.1rem;
    border: 1px solid #DCE5F1;
    border-radius: 24px;
    background: linear-gradient(
        115deg,
        #FFFFFF 0%,
        #F0F5FF 70%,
        #E7F0FF 100%
    );
    box-shadow: 0 8px 28px rgba(32,55,92,.055);
    margin-bottom: 1.5rem;
}

.hero-kicker {
    display: inline-block;
    padding: .32rem .65rem;
    border-radius: 999px;
    background: #E7EEFF;
    color: #3157A4;
    font-size: .76rem;
    font-weight: 750;
    letter-spacing: .075em;
    text-transform: uppercase;
    margin-bottom: .8rem;
}

.hero h1 {
    margin: 0;
    color: #15223A;
    font-size: clamp(2rem, 4vw, 2.8rem);
    line-height: 1.1;
    letter-spacing: -.045em;
}

.hero p {
    max-width: 680px;
    margin: .7rem 0 0;
    color: #5A6880;
    font-size: 1.04rem;
    line-height: 1.65;
}

.section-heading {
    font-size: 1.17rem;
    font-weight: 760;
    letter-spacing: -.02em;
    color: #1A2942;
    margin-bottom: .2rem;
}

.section-subtitle {
    color: #64748B;
    font-size: .9rem;
    margin: 0 0 .85rem;
    line-height: 1.5;
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
}

.stTextArea textarea {
    background: #FFFFFF !important;
    color: #172033 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px !important;
    line-height: 1.6 !important;
    padding: 1rem !important;
    min-height: 300px;
    box-shadow: inset 0 1px 2px rgba(15,23,42,.025);
}

.stTextArea textarea:focus {
    border-color: #6488D8 !important;
    box-shadow: 0 0 0 3px rgba(100,136,216,.15) !important;
}

.stSelectbox [data-baseweb="select"] > div,
.stRadio [role="radiogroup"] label,
.stCheckbox label {
    border-radius: 10px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.82);
    border: 1px solid #E0E7F0 !important;
    border-radius: 18px !important;
    padding: 1rem 1.1rem;
    box-shadow: 0 4px 18px rgba(27,48,80,.035);
    min-width: 0;
}

.stButton > button,
.stDownloadButton > button {
    width: 100%;
    border-radius: 12px !important;
    min-height: 2.85rem !important;
    font-weight: 700 !important;
    white-space: normal !important;
    transition: background .16s ease, border-color .16s ease !important;
    box-shadow: 0 2px 5px rgba(22,39,68,.06) !important;
}

.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: #315CCB !important;
    color: #FFFFFF !important;
    border: 1px solid #315CCB !important;
}

.stButton > button[kind="primary"] p,
.stDownloadButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stDownloadButton > button[kind="primary"] span {
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    background: #244BAF !important;
    border-color: #244BAF !important;
}

.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
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
    background: #FFFFFF;
    border: 1px solid #E0E7F0;
    padding: 1rem;
    border-radius: 14px;
    box-shadow: 0 3px 12px rgba(27,48,80,.035);
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
    border-radius: 12px;
    box-shadow: 0 8px 22px rgba(27,48,80,.09);
}

hr {
    border-color: #E1E7F0 !important;
}

/* Tablet and phone layouts */
@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: .9rem;
    }
}

@media (max-width: 700px) {
    .block-container {
        padding: 1rem .85rem 2.5rem;
    }

    .hero {
        padding: 1.35rem 1.2rem;
        border-radius: 18px;
    }

    .hero p {
        font-size: .95rem;
    }

    .stTextArea textarea {
        min-height: 260px;
        font-size: 16px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        margin-bottom: .6rem;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 46px !important;
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
    your paper, ink, and typography, then preview and export your notes as a PDF.</p>
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------- Sidebar ------------------------------------

with st.sidebar:
    st.header("Textify AI")
    st.caption("Turn text into handwritten-style pages and export them.")

    st.markdown(
        "**How it works**\n"
        "1. Paste or type your text.\n"
        "2. Customize your pages.\n"
        "3. Generate and download your pages."
    )

    st.info(
        "Handwriting fonts change the appearance of text; "
        "they do not reproduce real pen strokes."
    )


# ------------------------------ Session state --------------------------------

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
        "\n\nReplace this sample with your own study material."
    )


# ------------------------------- Main layout ---------------------------------

st.markdown(
    '<div class="section-heading">01 &nbsp; Your content</div>'
    '<div class="section-subtitle">Paste or type the text you want to turn into handwriting.</div>',
    unsafe_allow_html=True,
)

source_text = st.text_area(
    "Study material",
    key="source_text",
    height=390,
    max_chars=100000,
    placeholder="Paste your study material here...",
)

st.caption(
    f"{len(source_text):,} characters · "
    "Your text stays editable until you generate the pages."
)

st.divider()

st.markdown(
    '<div class="section-heading">02 &nbsp; Customize your pages</div>'
    '<div class="section-subtitle">Choose your paper, typography, and ink. Settings are grouped for easier scanning.</div>',
    unsafe_allow_html=True,
)

settings_a, settings_b, settings_c = st.columns(3, gap="large")

with settings_a:
    with st.container(border=True):
        st.markdown("**Paper & layout**")

        paper_style = st.selectbox(
            "Paper style",
            ["Ruled notebook", "Plain paper", "Grid", "Dotted", "Margin line"],
        )

        paper_color = st.selectbox("Paper color", list(PAPERS.keys()))
        page_name = st.selectbox("Page size", list(PAGE_SIZES.keys()))

        orientation = st.selectbox(
            "Page orientation",
            ["Portrait", "Landscape"],
            index=0,
            help="Portrait is vertical; Landscape is horizontal.",
        )

with settings_b:
    with st.container(border=True):
        st.markdown("**Handwriting**")

        font_name = st.selectbox(
            "Handwriting font",
            list(FONT_URLS.keys()),
            help="If the selected font cannot download, a fallback font is used.",
        )

        font_size = st.slider("Text size", 20, 54, 34)
        line_gap = st.slider("Line spacing", 32, 78, 56, step=2)

        with st.expander("Advanced typography"):
            letter_spacing = st.slider("Letter spacing", -1, 4, 0)
            word_spacing = st.slider("Extra word spacing", 0, 3, 0)
            margin_pct = st.slider("Page margins", 5, 12, 8)

            variation = st.checkbox(
                "Add natural layout variation",
                value=True,
                help="Slightly varies line placement for a more natural look.",
            )

with settings_c:
    with st.container(border=True):
        st.markdown("**Ink & finish**")

        ink_label = st.radio(
            "Ink color",
            list(INKS.keys()),
            horizontal=False,
        )

        ink = INKS[ink_label]

        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:10px;
padding:12px;border:1px solid #DCE5F0;border-radius:10px;
background:#F8FAFD;margin-top:8px;">
<span style="width:18px;height:18px;border-radius:50%;
background:{ink};border:2px solid white;
box-shadow:0 0 0 1px #AAB6C8;display:inline-block;flex-shrink:0"></span>
<span style="color:#26344B">Selected ink: <b>{ink_label}</b></span>
</div>
""",
            unsafe_allow_html=True,
        )

        st.caption(
            "Handwriting fonts change the appearance of text; "
            "they do not reproduce real pen strokes."
        )


# --------------------------- Generate notebook pages -------------------------

st.divider()

go, hint = st.columns([1, 1.05], vertical_alignment="center")

with go:
    generate = st.button(
        "✨ Generate notebook pages",
        type="primary",
        use_container_width=True,
    )

with hint:
    st.caption("Your text is rendered into handwritten-style pages.")


if generate:
    if not source_text.strip():
        st.error("Add some text before generating.")

    else:
        with st.spinner("Preparing font and rendering pages..."):
            ready = ensure_font(font_name)

            if not ready:
                st.warning(
                    f"Could not download {font_name}; "
                    "a fallback font will be used."
                )

            try:
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

                st.session_state.pages = pages
                st.session_state.pdf = to_pdf(pages)

                st.session_state.render_meta = {
                    "paper": paper_style,
                    "characters": len(source_text),
                }

                st.success(
                    f"Generated {len(pages)} page(s). Review before exporting."
                )

            except Exception as error:
                st.error(f"Could not generate pages: {error}")


# ------------------------------ Preview & export -----------------------------

if "pages" in st.session_state:
    pages = st.session_state.pages
    meta = st.session_state.get("render_meta", {})

    st.divider()

    st.markdown(
        '<div class="section-heading">03 &nbsp; Preview and export</div>'
        '<div class="section-subtitle">Review your pages before downloading the finished PDF.</div>',
        unsafe_allow_html=True,
    )

    metric_a, metric_b, metric_c = st.columns(3)

    metric_a.metric("Pages generated", len(pages))
    metric_b.metric(
        "Characters rendered",
        f"{meta.get('characters', 0):,}",
    )
    metric_c.metric("Paper style", meta.get("paper", "—"))

    st.caption(
        "Previewing up to the first three pages. "
        "The PDF includes every generated page."
    )

    preview_count = min(len(pages), 3)

    for start in range(0, preview_count, 2):
        columns = st.columns(min(2, preview_count - start))

        for offset, column in enumerate(columns):
            with column:
                page_index = start + offset

                st.image(
                    pages[page_index],
                    caption=f"Page {page_index + 1}",
                    use_container_width=True,
                )

    if len(pages) > 3:
        st.info(
            f"{len(pages) - 3} additional page(s) are included in the PDF."
        )

    st.download_button(
        "⬇️ Download complete PDF",
        st.session_state.pdf,
        file_name="textify_ai_handwritten_notes.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------- Footer -----------------------------------

st.divider()

st.caption(
    "Handwriting-style pages are rendered images, so PDF text may not "
    "be selectable or searchable."
)
