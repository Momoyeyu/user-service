from unittest.mock import patch

from src.common.email import send_email, send_verification_code


class TestSendVerificationCode:
    def test_no_api_key(self, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "")
        result = send_verification_code("user@test.com", "123456", "register")
        assert result is False

    @patch("src.common.email.resend")
    def test_register_purpose(self, mock_resend, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "re_test_key")
        monkeypatch.setattr("src.common.email.settings.EMAIL_FROM", "noreply@test.com")
        mock_resend.Emails.send.return_value = {"id": "msg_123"}

        result = send_verification_code("user@test.com", "123456", "register")

        assert result is True
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == "user@test.com"
        assert "Registration" in call_args["subject"]
        assert "123456" in call_args["html"]

    @patch("src.common.email.resend")
    def test_reset_password_purpose(self, mock_resend, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "re_test_key")
        monkeypatch.setattr("src.common.email.settings.EMAIL_FROM", "noreply@test.com")
        mock_resend.Emails.send.return_value = {"id": "msg_123"}

        result = send_verification_code("user@test.com", "654321", "reset_password")

        assert result is True
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert "Reset" in call_args["subject"]

    @patch("src.common.email.resend")
    def test_send_failure(self, mock_resend, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "re_test_key")
        mock_resend.Emails.send.side_effect = Exception("API error")

        result = send_verification_code("user@test.com", "123456", "register")
        assert result is False


class TestSendEmail:
    def test_no_api_key(self, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "")
        result = send_email("user@test.com", "Test", "<p>Hello</p>")
        assert result is False

    @patch("src.common.email.resend")
    def test_success(self, mock_resend, monkeypatch):
        monkeypatch.setattr("src.common.email.settings.RESEND_API_KEY", "re_test_key")
        monkeypatch.setattr("src.common.email.settings.EMAIL_FROM", "noreply@test.com")
        mock_resend.Emails.send.return_value = {"id": "msg_456"}

        result = send_email("user@test.com", "Subject", "<p>Body</p>")

        assert result is True
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["subject"] == "Subject"
        assert call_args["html"] == "<p>Body</p>"
