# ✍️ Textify AI

<p align="center"><b>Turn plain text into handwritten-style pages.</b><br>Customize handwriting fonts, paper styles, ink colors, page size, spacing, and margins, then preview and export your pages.</p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/Export-PDF-red" alt="PDF export">
</p>

## Features
- Convert typed or pasted text into handwriting-style page images.
- Choose handwriting fonts, paper styles, and ink colors.
- Customize page size, orientation, margins, and line spacing.
- Preview generated pages and download a multi-page PDF.
- No Gemini API key or AI service required.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Fonts are downloaded on first use when internet access is available; a fallback font is used if downloading fails.

## Deploy on Streamlit Community Cloud
1. Upload this repository to GitHub.
2. Create an app at https://share.streamlit.io/.
3. Select your repository, branch, and `app.py` as the main file.
4. Deploy. No Streamlit Secrets are required.

## Security
Do not upload real credentials or `.streamlit/secrets.toml` to GitHub.
