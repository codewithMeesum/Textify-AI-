
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
    "AI-generated notes should be reviewed before use. "
    "Handwriting-style pages are rendered images, so PDF text may not "
    "be selectable or searchable."
)
