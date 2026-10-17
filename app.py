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
    """Download the selected handwriting font if it is not available locally."""
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

            # Handle unusually long words without overflowing the page.
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

    for paragraph in (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    ):
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

            x = margin_left + (
                rng.randint(-3, 4) if variation else 0
            )
            adjusted_y = y + (
                rng.randint(-2, 2) if variation else 0
            )

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
.stApp {background:#F4F7FB;color:#172033}
.block-container {max-width:1250px;padding-top:1.5rem;padding-bottom:3rem}
.hero {padding:1.5rem 1.7rem;border:1px solid #DCE5F0;border-radius:20px;
background:linear-gradient(135deg,#fff,#EEF4FF);margin-bottom:1.2rem}
.hero h1 {margin:0;color:#172033;font-size:2.35rem;letter-spacing:-.03em}
.hero p {margin:.45rem 0 0;color:#52627A;font-size:1rem}
.stApp label,.stApp [data-testid="stWidgetLabel"] p {
    color:#172033!important;font-weight:600!important;font-size:.94rem!important
}
.stApp [data-testid="stCaptionContainer"] {
    color:#52627A!important;font-size:.87rem!important
}
.stTextArea textarea {
    background:#fff!important;color:#172033!important;
    border:1px solid #C9D5E4!important;border-radius:12px!important
}
.stButton > button,
.stDownloadButton > button {
    border-radius:10px!important;
    min-height:2.75rem!important;
    font-weight:650!important;
    background:#FFFFFF!important;
    color:#24324A!important;
    border:1px solid #C8D4E4!important;
    opacity:1!important;
    box-shadow:0 1px 2px rgba(15,23,42,.06)!important
}
.stButton > button p,
.stDownloadButton > button p,
.stButton > button span,
.stDownloadButton > button span {
    color:#24324A!important;opacity:1!important
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background:#EAF1FB!important;color:#15243B!important;
    border-color:#8CA7CB!important
}
.stButton > button:focus,
.stDownloadButton > button:focus {
    outline:2px solid #6C91C5!important;outline-offset:2px!important
}
.stButton > button:disabled,
.stDownloadButton > button:disabled {
    background:#E9EEF5!important;color:#64748B!important;
    border-color:#D5DEEA!important;opacity:1!important
}
div[data-testid="stMetric"] {
    background:#fff;border:1px solid #DFE7F1;
    padding:.8rem;border-radius:12px
}
</style>

<div class="hero">
    <h1>✍️ Textify AI</h1>
    <p>Turn plain text into customizable handwritten-style pages.</p>
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

left, right = st.columns([1.08, 0.92], gap="large")

with left:
    st.subheader("01 · Your content")

    source_text = st.text_area(
        "Study material",
        key="source_text",
        height=330,
        max_chars=100000,
        placeholder="Paste your study material here...",
    )

    st.caption(f"{len(source_text):,} characters")


with right:
    st.subheader("02 · Customize your pages")
    st.caption("Each setting changes the generated output.")

    with st.container(border=True):
        paper_style = st.selectbox(
            "Paper style",
            [
                "Ruled notebook",
                "Plain paper",
                "Grid",
                "Dotted",
                "Margin line",
            ],
        )

        paper_color = st.selectbox(
            "Paper color",
            list(PAPERS.keys()),
        )

        font_name = st.selectbox(
            "Handwriting font",
            list(FONT_URLS.keys()),
            help=(
                "Fonts download on first use when internet access "
                "is available."
            ),
        )

        page_name = st.selectbox(
            "Page size",
            list(PAGE_SIZES.keys()),
        )

        orientation = st.selectbox(
            "Page orientation",
            ["Portrait", "Landscape"],
            index=0,
            help=(
                "Choose Portrait for a vertical page or Landscape "
                "for a horizontal page."
            ),
        )

        st.markdown("**Writing size**")

        font_size = st.slider(
            "Text size (pixels)",
            20,
            54,
            34,
        )

        st.markdown("**Line spacing**")

        line_gap = st.slider(
            "Distance between lines",
            32,
            78,
            56,
            step=2,
        )

        with st.expander("Advanced typography and layout"):
            letter_spacing = st.slider(
                "Letter spacing",
                -1,
                4,
                0,
            )

            word_spacing = st.slider(
                "Extra word spacing",
                0,
                3,
                0,
            )

            margin_pct = st.slider(
                "Page margins",
                5,
                12,
                8,
            )

            variation = st.checkbox(
                "Add natural layout variation",
                value=True,
                help=(
                    "Slightly varies line placement. Turn off "
                    "for consistent alignment."
                ),
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
padding:10px 12px;border:1px solid #DCE5F0;border-radius:10px;
background:#F8FAFD;margin-top:4px;">
<span style="width:18px;height:18px;border-radius:50%;
background:{ink};border:2px solid white;
box-shadow:0 0 0 1px #AAB6C8;display:inline-block"></span>
<span style="color:#26344B">Selected ink: <b>{ink_label}</b></span>
</div>
""",
            unsafe_allow_html=True,
        )

        st.caption(
            "A handwriting font changes text appearance; "
            "it does not simulate real pen strokes."
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
    st.caption(
        "Your text is rendered into handwritten-style pages."
    )


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
                    f"Generated {len(pages)} page(s). "
                    "Review before exporting."
                )

            except Exception as error:
                st.error(f"Could not generate pages: {error}")


# ------------------------------ Preview & export -----------------------------

if "pages" in st.session_state:
    pages = st.session_state.pages
    meta = st.session_state.get("render_meta", {})

    st.divider()
    st.subheader("03 · Preview and export")

    metric_a, metric_b, metric_c = st.columns(3)

    metric_a.metric("Pages generated", len(pages))

    metric_b.metric(
        "Characters rendered",
        f"{meta.get('characters', 0):,}",
    )

    metric_c.metric(
        "Paper style",
        meta.get("paper", "—"),
    )

    st.caption(
        "Previewing up to the first three pages. "
        "The PDF includes every generated page."
    )

    preview_count = min(len(pages), 3)

    for start in range(0, preview_count, 2):
        columns = st.columns(
            min(2, preview_count - start)
        )

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
            f"{len(pages) - 3} additional page(s) "
            "are included in the PDF."
        )

    st.download_button(
        "⬇️ Download complete PDF",
        st.session_state.pdf,
        file_name="textify_ai_notes.pdf",
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
