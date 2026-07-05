\# Invoice Intake Agent



\## Overview



This project is a Python invoice-intake agent built for the Info-Tech Research Group home assignment.



The application reads a local inbound email JSON file, identifies the attached invoice PDF, extracts invoice and purchase-processing data from the PDF text and rendered PDF image, and creates a Customer Service notification.



The project uses the OpenAI Agents SDK with two tools:



1\. `extract\_invoice\_data` - extracts structured invoice data from the email, PDF text, and rendered PDF page image.

2\. `produce\_customer\_service\_notification` - creates the outbound Customer Service notification files.



The assignment requires a local email/PDF workflow, structured extraction, and a Customer Service notification output. It also requires a clear README, uv setup, a runnable command, and reasonable error handling. 



\## Requirements Satisfied



This project satisfies the assignment requirements by:



\- Using `uv` to create and manage the Python project

\- Using `.env` for secrets such as `OPENAI\_API\_KEY`

\- Keeping `.env` out of GitHub through `.gitignore`

\- Providing a simple runnable entrypoint

\- Reading a local inbound email JSON file

\- Reading the attached local invoice PDF

\- Extracting from PDF text and a rendered PDF image

\- Producing a human-readable notification and structured JSON payload

\- Handling common errors such as missing email file, missing attachment, unreadable PDF, invalid model, and missing API key



\## Tech Stack



\- Python

\- uv

\- OpenAI Agents SDK

\- OpenAI Python SDK

\- PyMuPDF

\- Pydantic

\- python-dotenv



\## Project Structure



```text

invoice-intake-agent/

&#x20; main.py

&#x20; README.md

&#x20; pyproject.toml

&#x20; uv.lock

&#x20; .env.example

&#x20; .gitignore



&#x20; data/

&#x20;   input\_email.json

&#x20;   Invoice.pdf



&#x20; src/

&#x20;   invoice\_agent/

&#x20;     email\_loader.py

&#x20;     pdf\_extractor.py

&#x20;     invoice\_context.py

&#x20;     schemas.py

&#x20;     openai\_extractor.py

&#x20;     notification\_tool.py

&#x20;     agent\_workflow.py



&#x20; outputs/

&#x20;   .gitkeep



&#x20; logs/

&#x20;   .gitkeep

