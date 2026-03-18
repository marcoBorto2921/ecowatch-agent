import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_email(subject: str, html_content: str) -> bool:
    """Invia una email HTML via Gmail."""
    
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    # Crea il messaggio
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"EcoWatch 🌱 <{gmail_address}>"
    msg["To"] = recipient

    # Aggiungi il corpo HTML
    msg.attach(MIMEText(html_content, "html"))

    try:
        print(f"\n📧 Invio email a {recipient}...")
        
        # Connettiti a Gmail via SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, recipient, msg.as_string())
        
        print(f"  ✓ Email inviata!")
        return True

    except Exception as e:
        print(f"  ✗ Errore invio email: {e}")
        return False