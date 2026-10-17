# Textify AI ✍️

Textify AI turns typed or pasted text into customizable handwriting-style pages and exports them as a PDF. It also includes optional Gemini-powered Smart Notes.

## Features

- Paste or type study material (no file-upload feature)
- Handwriting-style font choices
- Customizable paper style, paper color, ink color, spacing, margins, page size, and orientation
- Preview generated pages
- Download a multi-page PDF
- Optional Gemini Smart Notes: study notes, summaries, key bullet points, and simplified language

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Create `.streamlit/secrets.toml` based on `.streamlit/secrets.toml.example`. Add your Google AI Studio API key:

   ```toml
   GEMINI_API_KEY = "YOUR_REAL_KEY"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```

6. Start the app:

   ```bash
   streamlit run app.py
   ```

The API key is read on the server from Streamlit Secrets. Users of the app do not need to enter their own key. Do not commit `.streamlit/secrets.toml` to GitHub.

## Deploy on Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, `README.md`, `.gitignore`, and `.streamlit/secrets.toml.example` to a GitHub repository.
2. Create a new app in Streamlit Community Cloud and select `app.py` as the entry point.
3. In the deployed app's **Settings → Secrets**, add:

   ```toml
   GEMINI_API_KEY = "YOUR_REAL_KEY"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```

4. Save and reboot the app. Never add the real key to a tracked file or commit it to GitHub.

## Important notes

- AI usage consumes the owner's Gemini API quota and may incur charges depending on the API account and current terms. Add rate limits before sharing the app widely.
- AI Smart Notes is optional; handwriting rendering and PDF export work without an API key.
- Exported PDF pages are images, so their text may not be selectable or searchable.
- Handwriting fonts are used when their font files are available. Otherwise the app falls back to a system font.
