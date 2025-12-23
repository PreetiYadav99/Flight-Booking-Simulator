import os
import smtplib
from email.message import EmailMessage

def send_email(to_email, subject, body):
    """Send email using SMTP configured via environment variables.
    Falls back to printing to console if SMTP is not configured.
    """
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', '587')) if os.environ.get('SMTP_PORT') else None
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')

    if not smtp_host or not smtp_user or not smtp_pass or not smtp_port:
        # Fallback: log to console
        print(f"[EMAIL-DRYRUN] To: {to_email} | Subject: {subject}\n{body}\n")
        return True

    try:
        msg = EmailMessage()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
