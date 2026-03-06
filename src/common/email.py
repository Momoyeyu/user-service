"""邮件发送服务 (基于 Resend)"""

import resend
from loguru import logger

from src.conf.config import settings

_TEMPLATES = {
    "register": (
        "Your Registration Code",
        "Welcome",
        "Your registration verification code is:",
        "If you did not request this, please ignore this email.",
    ),
    "reset_password": (
        "Password Reset Code",
        "Password Reset Request",
        "Your password reset verification code is:",
        "If you did not request this, please ignore this email. Your password will not be changed.",
    ),
}
_DEFAULT_TEMPLATE = ("Verification Code", "", "Your verification code is:", "")


def _build_html(code: str, title: str, message: str, footer: str) -> str:
    title_html = f"<h2>{title}</h2>" if title else ""
    footer_html = f'<p style="color: #666; font-size: 12px;">{footer}</p>' if footer else ""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        {title_html}
        <p>{message}</p>
        <p style="font-size: 32px; font-weight: bold; color: #4F46E5; letter-spacing: 4px;">{code}</p>
        <p>This code will expire in 5 minutes.</p>
        {footer_html}
    </div>
    """


def _send(to_email: str, subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("Resend API key not configured, skipping email send")
        return False
    resend.api_key = settings.RESEND_API_KEY
    try:
        result = resend.Emails.send({"from": settings.EMAIL_FROM, "to": to_email, "subject": subject, "html": html})
        logger.info(f"Email sent to {to_email}, id: {result.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_code(to_email: str, code: str, purpose: str = "verify") -> bool:
    """发送验证码邮件。支持 register / reset_password 两种模板。"""
    subject, title, message, footer = _TEMPLATES.get(purpose, _DEFAULT_TEMPLATE)
    prefix = f"{settings.APP_NAME} - " if settings.APP_NAME else ""
    return _send(to_email, f"{prefix}{subject}", _build_html(code, title, message, footer))


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """发送自定义 HTML 邮件。"""
    return _send(to_email, subject, html_content)
