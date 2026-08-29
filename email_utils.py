import smtplib
from email.message import EmailMessage

SENDER_EMAIL = "your email"
SENDER_PASSWORD = "......."  # Google App Password

def send_budget_alert(to_email: str, category: str, limit: float, total_spent: float):
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Budget Alert: Exceeded limit for {category}!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    content = f"""
    Hi there,

    Warning! You have exceeded your set budget limit.

    - Category: {category}
    - Budget Limit: ${limit}
    - Total Spent: ${total_spent}

    Please review your expenses.
    """
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
