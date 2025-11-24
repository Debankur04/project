# workflow/email_utils.py

import random
import os
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from dotenv import load_dotenv

load_dotenv()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# Configure Brevo
config = Configuration()
config.api_key['api-key'] = BREVO_API_KEY


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    html_content = f"""
    <h2>Your OTP Code</h2>
    <p>Your verification code is <strong>{otp}</strong>.</p>
    <p>This OTP is valid for <strong>5 minutes</strong>.</p>
    """

    api_instance = TransactionalEmailsApi(ApiClient(config))

    email_payload = SendSmtpEmail(
        sender={"email": "debankurdutta04@gmail.com", "name": "FoodApp"},
        to=[{"email": email}],
        subject="Your OTP Verification Code",
        html_content=html_content,
    )

    response = api_instance.send_transac_email(email_payload)
    return response
