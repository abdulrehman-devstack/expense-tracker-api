import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "ar4729189@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_budget_alert(to_email: str, category: str, limit: float, total_spent: float):
    if not SENDER_PASSWORD:
        print("❌ SENDER_PASSWORD missing in environment variables!")
        return

    msg = EmailMessage()
    msg['Subject'] = f"🚨 Budget Alert: Exceeded limit for {category}!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(f"""
Hi there,

Warning! You have exceeded your set budget limit.

- Category: {category}
- Budget Limit: ${limit:.2f}
- Total Spent: ${total_spent:.2f}

Please review your expenses.
    """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Alert email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")