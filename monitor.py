import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

TARGET_RATE = 67.0
AUD_AMOUNT = 5000

WISE_URL = "https://wise.com/rates/live?source=aud&target=inr"


def get_rate():
    response = requests.get(WISE_URL, timeout=30)
    response.raise_for_status()

    payload = response.json()
    if isinstance(payload, list) and payload:
        data = payload[0]
    elif isinstance(payload, dict):
        data = payload
    else:
        raise ValueError("Unexpected Wise API response format")

    return {
        "source": data["source"],
        "target": data["target"],
        "rate": float(data["value"]),
        "timestamp": datetime.fromtimestamp(data["time"] / 1000),
    }


def send_email(rate_data):

    sender = os.environ["EMAIL_FROM"]
    receiver = os.environ["EMAIL_TO"]
    password = os.environ["EMAIL_PASSWORD"]

    rate = rate_data["rate"]

    inr_amount = round(rate * AUD_AMOUNT, 2)

    subject = f"🚨 AUD → INR Alert ({rate})"

    body = f"""
Good news!

The Wise AUD → INR exchange rate has crossed your target.

Current Rate
------------
1 AUD = {rate}

Target Rate
-----------
{TARGET_RATE}

Estimated Transfer
------------------
A${AUD_AMOUNT} → ₹{inr_amount:,.2f}

Checked At
----------
{rate_data["timestamp"]}

Open Wise:
https://wise.com/

Happy transferring!
"""

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 465))

    print(f"Attempting to send email from {sender} to {receiver} via {smtp_host}:{smtp_port}")

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as smtp:
            smtp.login(sender, password)
            smtp.send_message(message)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


def main():
    print("Checking Wise rate...")

    rate_data = get_rate()

    rate = rate_data["rate"]

    print(f"Current Rate: {rate}")

    if rate >= TARGET_RATE:
        print("Threshold reached.")
        try:
            send_email(rate_data)
            print("Email sent.")
        except Exception as exc:
            print(f"Email failed to send: {exc}")
            print("Check SMTP settings and workflow logs for details.")
    else:
        print("Threshold not reached.")


if __name__ == "__main__":
    main()