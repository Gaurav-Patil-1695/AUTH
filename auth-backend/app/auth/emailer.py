from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _build_reset_link(raw_token: str) -> str:
    """Build the full password-reset URL from APP_BASE_URL and the raw token."""
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


def _build_plain_text_body(reset_link: str) -> str:
    return (
        "You requested a password reset for your account.\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_link}\n\n"
        "This link will expire in "
        f"{settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not request a password reset, you can safely ignore this email."
    )


def _build_html_body(reset_link: str) -> str:
    return (
        "<!DOCTYPE html>"
        "<html lang=\"en\">"
        "<head><meta charset=\"UTF-8\"><title>Password Reset</title></head>"
        "<body style=\"font-family:sans-serif;color:#111827;\">"
        "<p>You requested a password reset for your account.</p>"
        "<p>"
        f"<a href=\"{reset_link}\" style=\"color:#4f46e5;\">Reset your password</a>"
        "</p>"
        f"<p>This link will expire in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>"
        "<p>If you did not request a password reset, you can safely ignore this email.</p>"
        "</body></html>"
    )


def send_reset_email(to_email: str, raw_token: str) -> None:
    """Send a password-reset email to *to_email* containing a link built from *raw_token*.

    Uses SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM, and
    APP_BASE_URL from the application settings.

    The reset link is constructed as::

        {APP_BASE_URL}/reset-password?token={raw_token}
    """
    reset_link = _build_reset_link(raw_token)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email

    plain_part = MIMEText(_build_plain_text_body(reset_link), "plain", "utf-8")
    html_part = MIMEText(_build_html_body(reset_link), "html", "utf-8")

    # Per RFC 2046 the last part is preferred; attach HTML last.
    message.attach(plain_part)
    message.attach(html_part)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.ehlo()
        if settings.SMTP_TLS:
            smtp.starttls()
            smtp.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM, [to_email], message.as_string())
