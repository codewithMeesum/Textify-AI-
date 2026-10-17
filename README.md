# ✍️ Textify AI

<h3 align="center">Turn Plain Text Into Handwritten Notes.</h3>

<p align="center">
  <b>Write. Customize. Preview. Export.</b><br>
  Transform your text into beautiful handwritten-style pages with customizable paper, ink, fonts, and AI-powered smart notes.
</p>

<p align="center">
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Powered%20by-Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit"></a>
  <img src="https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/Export-PDF-red" alt="PDF Export">
</p>

<p align="center">
  <a href="YOUR_STREAMLIT_APP_URL">🚀 Live Demo</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-getting-started">Get Started</a> ·
  <a href="#-deployment">Deploy</a>
</p>

---

## 💡 What is Textify AI?

Textify AI is a Python-powered web application that transforms ordinary typed text into handwritten-style notes. Customize the appearance of your pages, preview the result, and export your notes as a PDF.

Whether you're preparing study notes, organizing information, or creating handwritten-style documents, Textify AI makes the process simple.

## ✨ Features

| Feature | What it does |
|---|---|
| ✍️ Handwriting styles | Render text using handwriting-style fonts |
| 🎨 Customization | Choose fonts, ink colors, and paper styles |
| 📄 Page settings | Adjust paper size, orientation, margins, and spacing |
| 👀 Live preview | Preview your generated handwritten pages |
| 📥 PDF export | Download your notes as a PDF |
| 🤖 AI Smart Notes | Use Google Gemini to help organize or improve text |

## 🛠️ Built With

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Pillow-Image%20Processing-6A5ACD?style=for-the-badge" alt="Pillow">
  <img src="https://img.shields.io/badge/Google%20Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini">
</p>

## 📸 Preview

<p align="center">
  <i>Add a screenshot of the actual Textify AI interface here.</i>
</p>

<!-- Upload a screenshot to your repository, then replace the comment above with:
<p align="center">
  <img src="assets/textify-ai-preview.png" alt="Textify AI application preview" width="850">
</p>
-->

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd textify-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API access

Create `.streamlit/secrets.toml` in your local project:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "YOUR_SUPPORTED_GEMINI_MODEL"
```

Use a model name supported by your Gemini API access and the application's request format.

### 4. Run Textify AI

```bash
streamlit run app.py
```

Open the local URL shown in your terminal.

## ☁️ Deployment

Deploy Textify AI using Streamlit Community Cloud:

1. Push your project files to GitHub.
2. Visit [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app from your repository.
4. Select the `main` branch and `app.py` as the entry point.
5. Open the app's settings and add your Gemini credentials under **Secrets**.
6. Deploy and test the application.

## 🔐 Security

- Never commit your real API key to GitHub.
- Exclude `.streamlit/secrets.toml` from version control.
- Use Streamlit Cloud Secrets for deployment credentials.
- Never share your API key in screenshots, logs, or public documentation.

## 🗺️ Project Structure

```text
textify-ai/
├── .streamlit/
│   └── secrets.toml.example
├── assets/
│   └── fonts/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 🌱 Future Improvements

- More handwriting styles and customization options
- Improved document formatting
- Additional language and typography support

## ⭐ Support the Project

If you find Textify AI useful, consider giving the repository a star ⭐ and sharing it with other students and developers.

<p align="center">
  <b>Made with Python, creativity, and AI. ✨</b>
</p>
