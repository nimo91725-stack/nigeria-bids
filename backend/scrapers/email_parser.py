"""
IMAP email parser — reads tender alert emails and extracts opportunities.
Configure IMAP credentials in .env.
"""
import hashlib
import re
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header
from datetime import datetime
from ..config import settings
from .base import ScrapedOpportunity

TRAVEL_KEYWORDS = [
    "travel", "airline", "hotel", "accommodation", "tour", "ticketing",
    "logistics", "visa", "flight", "hospitality", "car hire", "tmc",
]


def _decode_header(raw) -> str:
    parts = decode_header(raw or "")
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def _is_travel_related(text: str) -> bool:
    return any(kw in text.lower() for kw in TRAVEL_KEYWORDS)


async def scrape() -> list[ScrapedOpportunity]:
    if not settings.imap_host:
        return []

    results = []
    with IMAPClient(settings.imap_host, ssl=True) as client:
        client.login(settings.imap_user, settings.imap_password)
        client.select_folder(settings.imap_folder)

        # Fetch unseen emails from the last 7 days
        messages = client.search(["UNSEEN", "SUBJECT", "tender"])
        for uid, data in client.fetch(messages, ["RFC822"]).items():
            raw = data[b"RFC822"]
            msg = message_from_bytes(raw)
            subject = _decode_header(msg.get("Subject", ""))
            sender = _decode_header(msg.get("From", ""))

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            if not _is_travel_related(f"{subject} {body}"):
                continue

            ext_id = hashlib.md5(f"{uid}{subject}".encode()).hexdigest()
            results.append(
                ScrapedOpportunity(
                    title=subject,
                    organization=sender,
                    source_name="Email Alert",
                    source_url="",
                    external_id=f"email_{ext_id}",
                    description=body[:2000],
                    sector="Email",
                )
            )
    return results
