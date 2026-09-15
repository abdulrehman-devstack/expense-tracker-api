import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


def send_budget_alert(to_email: str, category: str, limit: float, total_spent: float):
    """
    Jab budget exceed ho jaye, user ko email alert bhejo.
    Gmail App Password chahiye .env mein.
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️  Email not sent: SENDER_EMAIL or SENDER_PASSWORD missing in .env")
        return

    msg = EmailMessage()
    msg["Subject"] = f"🚨 Budget Alert: {category} limit exceeded!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.set_content(f"""
Hi,

You have EXCEEDED your monthly budget limit.

━━━━━━━━━━━━━━━━━━━━━━━
  Category    : {category}
  Budget Limit: ${limit:.2f}
  Total Spent : ${total_spent:.2f}
  Over Budget : ${total_spent - limit:.2f}
━━━━━━━━━━━━━━━━━━━━━━━

Please review your expenses and adjust your spending.

— Expense Tracker
    """)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Budget alert email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")