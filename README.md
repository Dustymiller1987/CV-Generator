# CV-Generator

A Flask application for creating and downloading professional CVs, with optional AI-assisted CV improvements and job-specific cover letters.

## Features

- CV builder with multiple themes and PDF downloads
- Automatic professional summary generation
- AI suggestions to improve a CV, optionally tailored to a target role
- AI cover letters based on the CV, job title, job description, and extra instructions
- Review and edit AI-suggested CV content before applying it
- Locally saved CV history in the browser

## Run locally

Create and activate the Python 3.15 project environment, install dependencies, and start the app in PowerShell:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

AI writing uses an OpenAI-compatible Chat Completions API. Set the API key in the environment before starting the app:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
python app.py
```

The default model is `gpt-4o-mini`. To use another compatible model or API endpoint, set `OPENAI_MODEL` and optionally `OPENAI_BASE_URL` (the base URL should normally end in `/v1`). Configure these values in your hosting provider's environment settings for deployment; do not put API keys in source code or commit them.

AI features send the CV details and, when provided, the job details to the configured AI provider. The provider may charge for API use. Without `OPENAI_API_KEY`, the rest of the CV builder works, but AI writing is unavailable.
