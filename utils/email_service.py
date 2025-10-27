# customer_portal/utils/email_service.py
"""
Handles sending emails for the application.
"""

import smtplib
import ssl
from email.message import EmailMessage
from config import Config # Import Config class
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Set up Jinja environment to load email templates
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def _render_email_template(template_name, **context):
    """Helper function to render an email template."""
    try:
        template = jinja_env.get_template(template_name)
        return template.render(context)
    except Exception as e:
        print(f"❌ [Email] Error rendering template '{template_name}': {e}")
        return None

# === NEW: Welcome Email Function ===
def send_welcome_email(to_email, first_name, temp_password):
    """
    Sends a welcome email to a new customer with their temporary password.
    Includes Bcc if configured.
    """
    if not Config.SMTP_SERVER or not Config.SMTP_USERNAME:
        print("⚠️ [Email] SMTP settings not configured. Cannot send email.")
        return False, "Email server is not configured."

    subject = "Welcome to the WePackItAll Customer Portal"

    # Render the HTML body from the template
    body_html = _render_email_template(
        'email/welcome_email.html', # Use the new template
        first_name=first_name,
        temp_password=temp_password,
        # Ensure LOGIN_URL uses APP_BASE_URL if set, otherwise default
        login_url=os.getenv('APP_BASE_URL', 'http://localhost:5001') + '/login'
    )

    if not body_html:
        return False, "Could not render email template."

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_FROM
    msg['To'] = to_email

    # Add Bcc if configured
    if Config.EMAIL_BCC:
        msg['Bcc'] = Config.EMAIL_BCC
        print(f"ℹ️ [Email] Bcc'ing {Config.EMAIL_BCC}")

    # Set plain text content as fallback
    msg.set_content(
        f"Hello {first_name},\n\n"
        f"An account has been created for you on the WePackItAll Customer Portal.\n"
        f"Your new temporary password is: {temp_password}\n\n"
        f"Please log in and change it immediately.\n"
    )
    # Add HTML alternative
    msg.add_alternative(body_html, subtype='html')

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            if Config.SMTP_USE_TLS:
                server.starttls(context=context)
            if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                 server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ [Email] Welcome email sent to {to_email}")
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ [Email] SMTP Authentication Error: {e}. Check username/password in .env")
        return False, "Failed to send email due to authentication error."
    except smtplib.SMTPException as e:
        print(f"❌ [Email] SMTP error sending email to {to_email}: {e}")
        return False, "Failed to send email due to an SMTP error."
    except Exception as e:
        print(f"❌ [Email] Unknown error sending email: {e}")
        return False, "An unknown error occurred while sending the email."

# === END NEW ===

def send_password_reset_email(to_email, first_name, temp_password):
    """
    Sends an email to a customer with their new temporary password.
    Includes Bcc if configured.
    """
    if not Config.SMTP_SERVER or not Config.SMTP_USERNAME:
        print("⚠️ [Email] SMTP settings not configured. Cannot send email.")
        return False, "Email server is not configured."

    subject = "Your Customer Portal Password Has Been Reset"

    # Render the HTML body from the template
    body_html = _render_email_template(
        'email/password_reset.html',
        first_name=first_name,
        temp_password=temp_password,
        # Ensure LOGIN_URL uses APP_BASE_URL if set, otherwise default
        login_url=os.getenv('APP_BASE_URL', 'http://localhost:5001') + '/login'
    )

    if not body_html:
        return False, "Could not render email template."

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_FROM
    msg['To'] = to_email

    # === Add Bcc if configured ===
    if Config.EMAIL_BCC:
        msg['Bcc'] = Config.EMAIL_BCC
        print(f"ℹ️ [Email] Bcc'ing {Config.EMAIL_BCC}")
    # === END ===

    # Set plain text content as fallback
    msg.set_content(
        f"Hello {first_name},\n\n"
        f"Your password has been reset. Your new temporary password is: {temp_password}\n\n"
        f"Please log in and change it immediately.\n"
    )
    # Add HTML alternative
    msg.add_alternative(body_html, subtype='html')

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            if Config.SMTP_USE_TLS:
                server.starttls(context=context)
            # Ensure login happens *after* starttls if TLS is used
            if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                 server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            # send_message handles To, Cc, Bcc automatically
            server.send_message(msg)
        print(f"✅ [Email] Password reset email sent to {to_email}")
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ [Email] SMTP Authentication Error: {e}. Check username/password in .env")
        return False, "Failed to send email due to authentication error."
    except smtplib.SMTPException as e:
        print(f"❌ [Email] SMTP error sending email to {to_email}: {e}")
        return False, "Failed to send email due to an SMTP error."
    except Exception as e:
        print(f"❌ [Email] Unknown error sending email: {e}")
        return False, "An unknown error occurred while sending the email."