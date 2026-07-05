# Invoice Intake Agent

## Overview

This project is a Python invoice-intake agent built for the Info-Tech Research Group home assignment.

The application reads a local inbound email JSON file, identifies the attached invoice PDF, extracts invoice and purchase-processing data from PDF text and rendered PDF image content, and creates a Customer Service notification.

The project uses the OpenAI Agents SDK with two callable tools:

1. `extract_invoice_data` - extracts structured invoice data from the email, PDF text, and rendered PDF page image.
2. `produce_customer_service_notification` - creates the outbound Customer Service notification files.

## Requirements Satisfied

This project satisfies the assignment requirements by:

- Using `uv` to create and manage the Python project
- Using `.env` for secrets such as `OPENAI_API_KEY`
- Keeping `.env` out of GitHub through `.gitignore`
- Providing a simple runnable entrypoint
- Reading a local inbound email JSON file
- Reading the attached local invoice PDF
- Extracting from PDF text and a rendered PDF image
- Producing a human-readable notification and structured JSON payload
- Handling common errors such as missing email file, missing attachment, unreadable PDF, invalid model, and missing API key

## Tech Stack

- Python
- uv
- OpenAI Agents SDK
- OpenAI Python SDK
- PyMuPDF
- Pydantic
- python-dotenv

## Project Structure

```text
invoice-intake-agent/
  main.py
  README.md
  pyproject.toml
  uv.lock
  .env.example
  .gitignore

  data/
    input_email.json
    Invoice.pdf

  src/
    invoice_agent/
      email_loader.py
      pdf_extractor.py
      invoice_context.py
      schemas.py
      openai_extractor.py
      notification_tool.py
      agent_workflow.py

  outputs/
    .gitkeep

  logs/
    .gitkeep
```

## Setup Instructions

Clone the repository:

```bash
git clone https://github.com/ashadevi/invoice-intake-agent.git
cd invoice-intake-agent
```

Install dependencies:

```bash
uv sync
```

Create a local `.env` file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-mini
```

Important: `.env` is ignored by Git and should never be committed.

## How to Run

Dry run without using the OpenAI API:

```bash
uv run python main.py --email ./data/input_email.json --dry-run
```

Full run:

```bash
uv run python main.py --email ./data/input_email.json
```

The full run loads the email, resolves the PDF attachment, extracts PDF text, renders the first PDF page image, runs the invoice extraction workflow, and writes the Customer Service outputs.

## Output Files and Logs

After a successful full run, the project creates:

```text
outputs/outbound_email.txt
outputs/outbound_payload.json
logs/app.log
```

`outputs/outbound_email.txt` contains the human-readable Customer Service notification.

`outputs/outbound_payload.json` contains the structured JSON payload for downstream processing.

`logs/app.log` contains workflow logs for debugging and review.

Generated output files and logs are ignored by Git.

## Error Handling

The project includes error handling for:

- Missing email JSON file
- Invalid email JSON
- Missing `Message` object
- Missing attachment
- Missing PDF attachment
- PDF listed in the email but not found locally
- Unreadable PDF
- Unsupported image type
- Missing `OPENAI_API_KEY`
- Invalid model name
- OpenAI extraction failure
- Output file writing failure

## Model and Usage Notes

The assignment key is limited, so the project is designed to reduce unnecessary API usage.

The project supports only:

- `gpt-5-mini`
- `gpt-5-nano`

Cost-control choices:

- Local PDF text extraction happens before calling OpenAI
- The first PDF page is rendered once and reused
- The model receives a controlled text context and one rendered page image
- Dry-run mode validates local processing without API calls

## Design Explanation

The project separates the workflow into small modules:

- `email_loader.py` loads and validates the inbound email JSON.
- `pdf_extractor.py` validates the PDF, extracts text, and renders the first page image.
- `invoice_context.py` combines email and PDF context.
- `schemas.py` defines structured Pydantic models.
- `openai_extractor.py` performs targeted invoice extraction.
- `notification_tool.py` writes human-readable and JSON outputs.
- `agent_workflow.py` defines the OpenAI Agents SDK agent and its two tools.
- `main.py` provides the command-line entrypoint.

## Interview Walkthrough Summary

This project is an invoice-intake agent built with Python, uv, and the OpenAI Agents SDK. It reads a local email JSON file, resolves the attached invoice PDF, extracts structured invoice data from both PDF text and rendered image content, and creates a Customer Service notification with both a readable summary and structured JSON payload.

The project uses `.env` for secrets, `.gitignore` to protect the API key, dry-run mode to avoid unnecessary API usage, and clear error handling for common failures.

## Notes

The sample email and invoice PDF are treated as input data. Their full contents are not copied into this README or source code comments.