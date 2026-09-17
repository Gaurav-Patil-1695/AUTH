"""Tests for app.auth.emailer"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from app.auth import emailer as emailer_module
from app.auth.emailer import (
    _build_html_body,
    _build_plain_text_body,
    _build_reset_link,
    send_reset_email,
)
from app.config.settings import settings


# ---------------------------------------------------------------------------
# _build_reset_link
# ---------------------------------------------------------------------------

class TestBuildResetLink:
    def test_contains_token(self):
        link = _build_reset_link("mytoken")
        assert "mytoken" in link

    def test_contains_reset_password_path(self):
        link = _build_reset_link("tok")
        assert "/reset-password" in link

    def test_query_param_format(self):
        link = _build_reset_link("abc123")
        assert "token=abc123" in link

    def test_base_url_trailing_slash_stripped(self):
        with patch.object(settings, "APP_BASE_URL", "http://example.com/"):
            link = _build_reset_link("t")
        # Should not have double slash
        assert "//reset-password" not in link

    def test_starts_with_base_url(self):
        base = settings.APP_BASE_URL.rstrip("/")
        link = _build_reset_link("token")
        assert link.startswith(base)


# ---------------------------------------------------------------------------
# _build_plain_text_body
# ---------------------------------------------------------------------------

class TestBuildPlainTextBody:
    def test_contains_reset_link(self):
        link = "http://example.com/reset-password?token=abc"
        body = _build_plain_text_body(link)
        assert link in body

    def test_contains_expire_minutes(self):
        link = "http://example.com/reset-password?token=abc"
        body = _build_plain_text_body(link)
        assert str(settings.RESET_TOKEN_EXPIRE_MINUTES) in body

    def test_is_string(self):
        body = _build_plain_text_body("http://x.com")
        assert isinstance(body, str)

    def test_mentions_password_reset(self):
        body = _build_plain_text_body("http://x.com")
        assert "password reset" in body.lower()


# ---------------------------------------------------------------------------
# _build_html_body
# ---------------------------------------------------------------------------

class TestBuildHtmlBody:
    def test_contains_reset_link(self):
        link = "http://example.com/reset-password?token=tok"
        body = _build_html_body(link)
        assert link in body

    def test_contains_expire_minutes(self):
        body = _build_html_body("http://x.com")
        assert str(settings.RESET_TOKEN_EXPIRE_MINUTES) in body

    def test_is_html(self):
        body = _build_html_body("http://x.com")
        assert "<html" in body.lower()

    def test_contains_anchor_tag(self):
        link = "http://example.com/reset"
        body = _build_html_body(link)
        assert "<a href=" in body


# ---------------------------------------------------------------------------
# send_reset_email
# ---------------------------------------------------------------------------

class TestSendResetEmail:
    def _run_send(self, smtp_mock, to_email="user@example.com", raw_token="rawtoken"):
        send_reset_email(to_email, raw_token)

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_smtp_context_manager_used(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_reset_email("to@example.com", "tok")
        mock_smtp_cls.assert_called_once_with(settings.SMTP_HOST, settings.SMTP_PORT)

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_sendmail_called_with_correct_args(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_reset_email("recipient@example.com", "mytoken")

        smtp_instance.sendmail.assert_called_once()
        from_arg, to_arg, _ = smtp_instance.sendmail.call_args[0]
        assert from_arg == settings.SMTP_FROM
        assert "recipient@example.com" in to_arg

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_sendmail_body_contains_token(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_reset_email("x@y.com", "special_token_xyz")

        _, _, message_str = smtp_instance.sendmail.call_args[0]
        assert "special_token_xyz" in message_str

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_ehlo_called(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_reset_email("a@b.com", "t")
        smtp_instance.ehlo.assert_called()

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_starttls_called_when_tls_enabled(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(settings, "SMTP_TLS", True):
            send_reset_email("a@b.com", "t")
        smtp_instance.starttls.assert_called_once()

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_starttls_not_called_when_tls_disabled(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(settings, "SMTP_TLS", False):
            send_reset_email("a@b.com", "t")
        smtp_instance.starttls.assert_not_called()

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_login_called_when_credentials_present(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(settings, "SMTP_USERNAME", "user"), \
             patch.object(settings, "SMTP_PASSWORD", "pass"), \
             patch.object(settings, "SMTP_TLS", False):
            send_reset_email("a@b.com", "t")
        smtp_instance.login.assert_called_once_with("user", "pass")

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_login_not_called_when_no_credentials(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(settings, "SMTP_USERNAME", ""), \
             patch.object(settings, "SMTP_PASSWORD", ""), \
             patch.object(settings, "SMTP_TLS", False):
            send_reset_email("a@b.com", "t")
        smtp_instance.login.assert_not_called()

    @patch("app.auth.emailer.smtplib.SMTP")
    def test_subject_header(self, mock_smtp_cls):
        smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_reset_email("a@b.com", "t")
        _, _, message_str = smtp_instance.sendmail.call_args[0]
        assert "Reset your password" in message_str
