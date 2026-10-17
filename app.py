import io
import random
import textwrap
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ---------------------------- Page configuration ----------------------------
st.set_page_config(page_title="Textify AI", page_icon="✍️", layout="wide")

# ------------------------------- Styling ------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&family=Kalam:wght@300;400;700&family=Patrick+Hand&display=swap');
.stApp { background: #f7f8fc; }
.block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1250px; }
.hero { padding: 1.5rem 1.6rem; border: 1px solid #e4e7ef; border-radius: 18px; background: #ffffff; margin-bottom: 1.25rem; }
.hero h1 { margin: 0; color: #172033; font-size: 2.1rem; }
.hero p { color: #647084; margin: .35rem 0 0; }
div.stButton > button, div.stDownloadButton > button { background: #263b80 !important; color: #ffffff !important; border: 1px solid #263b80 !important; border-radius: 10px !important; font-weight: 600 !important; }
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #1b2c65 !important; color: #ffffff !important; border-color: #1b2c65 !important; }
[data-testid="stSidebar"] { background: #ffffff; }
.small-note { color: #687386; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>✍️ Textify AI</h1>
  <p>Turn your text into neat, handwriting-style pages — then preview and export as a PDF.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------ Constants -----------------------------------
PAPER_SIZES = {
    "A4": (794, 1123),
    "Letter": (816, 1056),
    "A5": (559, 794),
}
INK_COLORS = {
    "Blue": (35, 78, 160),
    "Black": (35, 38, 45),
    "Dark Green": (30, 100, 70),
    "Purple": (105, 62, 150),
}
PAPER_COLORS = {
    "White": (255, 255, 255),
    "Cream": (255, 251, 235),
    "Light Yellow": (255, 255, 220),
}

# PIL needs actual font files. These common local fonts are used when present.
# You can place handwriting .ttf files in a local "fonts" folder to use them.
FONT_FILES = {
    "Caveat": ["fonts/Caveat-Regular.ttf", "Caveat-Regular.ttf"],
    "Patrick Hand": ["fonts/PatrickHand-Regular.ttf", "PatrickHand-Regular.ttf"],
    "Kalam": ["fonts/Kalam-Regular.ttf", "Kalam-Regular.ttf"],
    "DejaVu Sans": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"],
}


def get_font(font_name: str, size: int):
    candidates = FONT_FILES.get(font_name, []) + FONT_FILES["DejaVu Sans"]
    for candidate in candidates:
        try:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def text_width(draw, text, font, letter_spacing=0):
    if not text:
        return 0
    if letter_spacing == 0:
        return draw.textlength(text, font=font)
    return sum(draw.textlength(char, font=font) for char in text) + letter_spacing * (len(text) - 1)


def draw_spaced_text(draw, xy, text, font, fill, letter_spacing=0):
    x, y = xy
    if letter_spacing == 0:
        draw.text((x, y), text, font=font, fill=fill)
        return
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + letter_spacing


def wrap_paragraph(draw, paragraph, font, max_width, letter_spacing=0):
    """Wrap text by measured pixel width, preserving paragraph breaks."""
    words = paragraph.split()
    if not words:
        return [""]
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if text_width(draw, candidate, font, letter_spacing) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        # Split unusually long words so they don't run off the page.
        if text_width(draw, word, font, letter_spacing) > max_width:
            part = ""
            for char in word:
                test = part + char
                if part and text_width(draw, test, font, letter_spacing) > max_width:
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


def render_pages(text, options):
    page_w, page_h = PAPER_SIZES[options["page_size"]]
    if options["orientation"] == "Landscape":
        page_w, page_h = page_h, page_w

    margin_left = int(options["margin_left"] * page_w / 100)
    margin_right = int(options["margin_right"] * page_w / 100)
    margin_top = int(options["margin_top"] * page_h / 100)
    margin_bottom = int(options["margin_bottom"] * page_h / 100)
    content_w = max(100, page_w - margin_left - margin_right)
    content_bottom = page_h - margin_bottom

    font_size = int(options["font_size"])
    font = get_font(options["font"], font_size)
    paper = PAPER_COLORS[options["paper_color"]]
    ink = INK_COLORS[options["ink_color"]]
    line_gap = int(font_size * (options["line_spacing"] / 100))
    line_height = font_size + line_gap
    letter_spacing = int(options["letter_spacing"])
    rng = random.Random(27)  # stable preview/export variation

    paragraphs = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    pages, current_y = [], margin_top
    page = Image.new("RGB", (page_w, page_h), paper)
    draw = ImageDraw.Draw(page)

    def draw_paper(d):
        style = options["paper_style"]
        line_color = (202, 218, 239) if options["paper_color"] != "White" else (211, 225, 243)
        if style in ("Ruled", "Margin line"):
            y = margin_top
            while y < page_h - margin_bottom:
                d.line((0, y, page_w, y), fill=line_color, width=1)
                y += max(18, int(options["rule_spacing"]))
        elif style == "Grid":
            spacing = max(18, int(options["rule_spacing"]))
            for x in range(0, page_w, spacing):
                d.line((x, 0, x, page_h), fill=(225, 229, 235), width=1)
            for y in range(0, page_h, spacing):
                d.line((0, y, page_w, y), fill=(225, 229, 235), width=1)
        elif style == "Dotted":
            spacing = max(18, int(options["rule_spacing"]))
            for y in range(spacing, page_h, spacing):
                for x in range(spacing, page_w, spacing):
                    d.ellipse((x, y, x + 1, y + 1), fill=(190, 201, 216))
        if style == "Margin line":
            x = margin_left - 14
            d.line((x, 0, x, page_h), fill=(226, 130, 140), width=2)

    draw_paper(draw)

    for p_index, paragraph in enumerate(paragraphs):
        wrapped = wrap_paragraph(draw, paragraph, font, content_w, letter_spacing)
        if paragraph == "":
            wrapped = [""]
        for line in wrapped:
            if current_y + line_height > content_bottom:
                pages.append(page)
                page = Image.new("RGB", (page_w, page_h), paper)
                draw = ImageDraw.Draw(page)
                draw_paper(draw)
                current_y = margin_top
            if line:
                offset = rng.randint(-1, 1) if options["variation"] else 0
                draw_spaced_text(draw, (margin_left, current_y + offset), line, font, ink, letter_spacing)
            current_y += line_height
        # Add a small gap between paragraphs, without making empty lines huge.
        if p_index < len(paragraphs) - 1:
            current_y += int(font_size * 0.25)

    pages.append(page)

    # Small footer branding, kept subtle and within the bottom margin.
    if options["footer"]:
        for i, pg in enumerate(pages):
            d = ImageDraw.Draw(pg)
            footer_font = get_font("DejaVu Sans", 12)
            label = f"Created with Textify AI  •  Page {i + 1}"
            d.text((page_w - margin_right - d.textlength(label, font=footer_font), page_h - max(24, margin_bottom // 2)),
                   label, font=footer_font, fill=(125, 130, 140))
    return pages


def make_pdf(pages):
    output = io.BytesIO()
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(output, format="PDF", save_all=True, append_images=rgb_pages[1:], resolution=150)
    output.seek(0)
    return output.getvalue()


def make_text_download(text):
    return text.encode("utf-8")

# ---------------------------------- UI --------------------------------------
with st.sidebar:
    st.header("Page & handwriting")
    font_choice = st.selectbox("Handwriting font", ["Caveat", "Patrick Hand", "Kalam", "DejaVu Sans"])
    font_size = st.slider("Font size", 16, 42, 25)
    line_spacing = st.slider("Line spacing", 0, 100, 40, help="Higher values add more space between lines.")
    letter_spacing = st.slider("Letter spacing", 0, 4, 0)
    variation = st.checkbox("Slight writing variation", value=True)

    st.divider()
    paper_style = st.selectbox("Paper style", ["Ruled", "Plain", "Grid", "Dotted", "Margin line"])
    paper_color = st.selectbox("Paper color", list(PAPER_COLORS.keys()))
    rule_spacing = st.slider("Rule / grid spacing", 20, 48, 32)
    ink_color = st.selectbox("Ink color", list(INK_COLORS.keys()))

    st.divider()
    page_size = st.selectbox("Page size", list(PAPER_SIZES.keys()), index=0)
    orientation = st.selectbox("Page orientation", ["Portrait", "Landscape"])
    margin_left = st.slider("Left margin (%)", 5, 18, 10)
    margin_right = st.slider("Right margin (%)", 5, 18, 9)
    margin_top = st.slider("Top margin (%)", 5, 18, 8)
    margin_bottom = st.slider("Bottom margin (%)", 5, 18, 8)
    footer = st.checkbox("Add Textify AI footer", value=True)

st.subheader("1. Enter your text")
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
source_text = st.text_area(
    "Type or paste your text below",
    key="source_text",
    height=260,
    placeholder="Start typing or paste your notes here...",
    label_visibility="collapsed",
)

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("Clear text", use_container_width=True):
        st.session_state.source_text = ""
        st.rerun()
with col_b:
    st.download_button(
        "Download original text (.txt)",
        data=make_text_download(source_text),
        file_name="textify_ai_text.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=not source_text.strip(),
    )

# Optional AI Smart Notes. Uses the owner's private Gemini API key from Streamlit Secrets.
with st.expander("Optional: AI Smart Notes", expanded=False):
    st.caption("Generate study notes, summaries, key points, or simpler explanations with Gemini.")
    ai_task = st.selectbox(
        "What should AI do?",
        ["Create concise study notes", "Summarize", "Make key bullet points", "Simplify the language"],
    )
    if st.button("Generate AI notes", disabled=not source_text.strip(), use_container_width=True):
        if len(source_text) > 30000:
            st.warning("Please keep the text under 30,000 characters for AI note generation.")
        else:
            try:
                import requests

                api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
                model_name = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
                if not api_key:
                    st.error("AI Smart Notes is not configured yet. The app owner must add GEMINI_API_KEY in Streamlit Secrets.")
                else:
                    instruction = {
                        "Create concise study notes": "Create clear, concise study notes with headings and key concepts.",
                        "Summarize": "Summarize the text accurately and concisely.",
                        "Make key bullet points": "Turn the text into well-organized key bullet points.",
                        "Simplify the language": "Rewrite the text in simple, beginner-friendly language without changing its meaning.",
                    }[ai_task]
                    with st.spinner("Gemini is preparing your notes..."):
                        response = requests.post(
                            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_name,
                                "messages": [
                                    {"role": "system", "content": instruction + " Preserve important facts and do not invent information."},
                                    {"role": "user", "content": source_text},
                                ],
                                "temperature": 0.3,
                            },
                            timeout=60,
                        )
                        if not response.ok:
                            # Avoid showing any credentials in errors; provider response text is truncated.
                            raise RuntimeError(f"Gemini request failed ({response.status_code}). Check the model, API key, or quota in Google AI Studio.")
                        result = response.json()["choices"][0]["message"]["content"]
                        if not isinstance(result, str) or not result.strip():
                            raise RuntimeError("Gemini returned empty notes. Please try again.")
                        st.session_state["ai_notes_result"] = result.strip()
                    st.success("AI notes generated. Review them below before using them.")
            except Exception as exc:
                st.error(f"Could not generate AI notes: {exc}")
    if st.session_state.get("ai_notes_result"):
        st.text_area(
            "Generated notes",
            key="ai_notes_result_display",
            value=st.session_state["ai_notes_result"],
            height=200,
        )
        if st.button("Use AI notes as source text", use_container_width=True):
            st.session_state.source_text = st.session_state["ai_notes_result"]
            st.rerun()

st.subheader("2. Preview and export")
if not source_text.strip():
    st.info("Enter some text above to preview your handwriting-style pages.")
else:
    options = {
        "font": font_choice,
        "font_size": font_size,
        "line_spacing": line_spacing,
        "letter_spacing": letter_spacing,
        "variation": variation,
        "paper_style": paper_style,
        "paper_color": paper_color,
        "rule_spacing": rule_spacing,
        "ink_color": ink_color,
        "page_size": page_size,
        "orientation": orientation,
        "margin_left": margin_left,
        "margin_right": margin_right,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "footer": footer,
    }
    pages = render_pages(source_text, options)
    st.caption(f"Preview: {len(pages)} page(s)  •  {page_size} {orientation.lower()}")
    preview_col, details_col = st.columns([1.2, 1])
    with preview_col:
        st.image(pages[0], caption="Page 1 preview", use_container_width=True)
    with details_col:
        st.markdown("#### Your settings")
        st.write(f"**Font:** {font_choice}")
        st.write(f"**Ink:** {ink_color}")
        st.write(f"**Paper:** {paper_style} · {paper_color}")
        st.write(f"**Page:** {page_size} · {orientation}")
        st.write(f"**Pages:** {len(pages)}")
        st.markdown("<p class='small-note'>PDF pages are rendered as page images, so text in the exported PDF may not be selectable or searchable.</p>", unsafe_allow_html=True)
        st.download_button(
            "Download handwritten PDF",
            data=make_pdf(pages),
            file_name="textify_ai_handwriting.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.divider()
st.caption("Textify AI · Handwriting-style rendering, not a scan of real handwriting.")
