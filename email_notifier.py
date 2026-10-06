"""Gmail SMTP email notifications."""

import smtplib
from email.message import EmailMessage
from config import settings

def send_job_alert(item, categories):
    if not settings.EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_PASSWORD is not set. Create a Gmail App Password and put it "
            "in the EMAIL_PASSWORD environment variable / GitHub Secret."
        )

    category_text = " + ".join(categories)
    subject = f"🚨 New {category_text} Role: {item.company} — {item.title}"

    body = f"""New job detected by your internship/new-grad tracker.

CATEGORY
{category_text}

COMPANY
{item.company}

ROLE
{item.title}

LOCATION
{item.location or "Not listed"}

POSTED
{item.posted_date or "Not listed"}

SOURCE
{item.source}

APPLICATION
{item.url}

This role matched your SWE / Quant Developer / Game Development alert filters.
"""

    msg = EmailMessage()
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = settings.ALERT_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.login(settings.SENDER_EMAIL, settings.EMAIL_PASSWORD)
        smtp.send_message(msg)
