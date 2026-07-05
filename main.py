import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.invoice_agent.agent_workflow import AgentWorkflowError, run_invoice_agent
from src.invoice_agent.invoice_context import build_invoice_context, build_model_text_context


LOG_FILE = Path("logs/app.log")


def setup_logging() -> None:
    """Configure application logging."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Invoice-intake agent for processing a local email JSON and invoice PDF."
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Path to the inbound email JSON file, e.g. ./data/input_email.json",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override. Allowed: gpt-5-mini or gpt-5-nano.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare local email/PDF context without calling OpenAI.",
    )

    return parser.parse_args()


def validate_environment(dry_run: bool) -> None:
    """
    Validate required environment configuration.

    In dry-run mode, OPENAI_API_KEY is not required because no API call is made.
    """
    load_dotenv()

    if dry_run:
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise AgentWorkflowError(
            "OPENAI_API_KEY is missing. Add it to your local .env file."
        )


async def main_async() -> int:
    """Run the command-line workflow."""
    setup_logging()
    args = parse_args()

    email_path = Path(args.email)

    try:
        logging.info("Starting invoice-intake workflow.")
        logging.info("Email path: %s", email_path)

        validate_environment(dry_run=args.dry_run)

        if args.dry_run:
            logging.info("Running dry-run mode. No OpenAI API call will be made.")

            context = build_invoice_context(email_path)
            model_context = build_model_text_context(context)

            print("\nDry run completed successfully.")
            print(f"Email subject: {context['email_summary']['subject']}")
            print(f"PDF path: {context['pdf_path']}")
            print(f"First page image: {context['pdf_content']['first_page_image']}")
            print(f"Prepared model context length: {len(model_context)}")
            print(f"Log file: {LOG_FILE}")

            logging.info("Dry-run completed successfully.")
            return 0

        final_output = await run_invoice_agent(email_path=email_path, model=args.model)

        print("\nInvoice intake completed successfully.")
        print(final_output)
        print("\nExpected output files:")
        print("- outputs/outbound_email.txt")
        print("- outputs/outbound_payload.json")
        print(f"- {LOG_FILE}")

        logging.info("Invoice-intake workflow completed successfully.")
        return 0

    except Exception as exc:
        logging.exception("Invoice-intake workflow failed.")
        print(f"\nError: {exc}")
        print(f"See log file for details: {LOG_FILE}")
        return 1


def main() -> None:
    """Synchronous entrypoint for the script."""
    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
