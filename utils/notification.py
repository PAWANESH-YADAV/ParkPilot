"""
ParkPilot — Notification System
Sends alerts via SMS (Twilio), Email (SMTP), Push (FCM), and WhatsApp.
Used by surveillance, billing, and dynamic pricing modules.
"""

import smtplib
import json
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from utils.logger import get_logger
from utils.config import settings

logger = get_logger("parkpilot.notification")


# ═══════════════════════════════════════════════════════════════════════════
#  SMS — Twilio
# ═══════════════════════════════════════════════════════════════════════════

def send_sms(to_phone: str, message: str) -> bool:
    """
    Send an SMS via Twilio.

    Args:
        to_phone: Recipient phone number (E.164 format, e.g. '+919876543210')
        message: SMS body text

    Returns:
        True on success, False on failure
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured — SMS not sent")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        logger.info(f"SMS sent to {to_phone} | SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"SMS failed to {to_phone}: {e}")
        return False


def send_whatsapp(to_phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio WhatsApp API.

    Args:
        to_phone: Recipient phone (E.164 format)
        message: Message body
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN]):
        logger.warning("Twilio credentials not configured — WhatsApp not sent")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{to_phone}"
        )
        logger.info(f"WhatsApp sent to {to_phone} | SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp failed to {to_phone}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Email — SMTP
# ═══════════════════════════════════════════════════════════════════════════

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    attachment_path: str = None
) -> bool:
    """
    Send an HTML email with optional file attachment.

    Args:
        to_email: Recipient email
        subject: Email subject
        body_html: HTML body content
        attachment_path: Optional file path to attach (e.g. PDF bill)

    Returns:
        True on success, False on failure
    """
    if not all([settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD]):
        logger.warning("Email credentials not configured — email not sent")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"ParkPilot <{settings.EMAIL_USERNAME}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))

        if attachment_path:
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                import os
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}"
                )
                msg.attach(part)

        with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USERNAME, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email} | Subject: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Push Notification — Firebase Cloud Messaging (FCM)
# ═══════════════════════════════════════════════════════════════════════════

def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """
    Send a push notification via Firebase Cloud Messaging.

    Args:
        device_token: FCM device registration token
        title: Notification title
        body: Notification body text
        data: Optional extra data payload dict

    Returns:
        True on success, False on failure
    """
    if not settings.FCM_SERVER_KEY:
        logger.warning("FCM server key not configured — push not sent")
        return False

    try:
        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": 1
            },
            "data": data or {}
        }
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"Push notification sent | Title: {title}")
            return True
        else:
            logger.error(f"FCM error: {response.status_code} — {response.text}")
            return False
    except Exception as e:
        logger.error(f"Push notification failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience — Security Alert
# ═══════════════════════════════════════════════════════════════════════════

def send_security_alert(
    event_type: str,
    location: str,
    timestamp: datetime,
    camera_id: str,
    security_phone: str = None,
    security_email: str = None,
    security_fcm_token: str = None
):
    """
    Broadcast a security alert via all configured channels.

    Args:
        event_type: e.g. 'LOITERING', 'VANDALISM', 'UNAUTHORIZED_ACCESS'
        location: e.g. 'Zone B, Camera 3'
        timestamp: Event timestamp
        camera_id: Camera identifier
        security_phone: Security guard's phone
        security_email: Security email
        security_fcm_token: Security app FCM token
    """
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    sms_msg = (
        f"🚨 PARKPILOT ALERT\n"
        f"Type: {event_type}\n"
        f"Location: {location}\n"
        f"Camera: {camera_id}\n"
        f"Time: {ts_str}"
    )
    email_html = f"""
    <html><body style="font-family:Arial;background:#1a1a2e;color:#eee;padding:20px">
    <div style="max-width:600px;margin:auto;background:#16213e;border-radius:12px;padding:30px">
        <h1 style="color:#e94560">🚨 Security Alert</h1>
        <table style="width:100%;border-collapse:collapse">
            <tr><td style="padding:8px;color:#aaa">Event Type</td>
                <td style="padding:8px;color:#e94560;font-weight:bold">{event_type}</td></tr>
            <tr><td style="padding:8px;color:#aaa">Location</td>
                <td style="padding:8px">{location}</td></tr>
            <tr><td style="padding:8px;color:#aaa">Camera</td>
                <td style="padding:8px">{camera_id}</td></tr>
            <tr><td style="padding:8px;color:#aaa">Time</td>
                <td style="padding:8px">{ts_str}</td></tr>
        </table>
        <p style="color:#aaa;margin-top:20px">ParkPilot Autonomous Parking System</p>
    </div></body></html>
    """

    if security_phone:
        send_sms(security_phone, sms_msg)
        send_whatsapp(security_phone, sms_msg)

    if security_email:
        send_email(
            security_email,
            f"🚨 ParkPilot Security Alert — {event_type}",
            email_html
        )

    if security_fcm_token:
        send_push_notification(
            security_fcm_token,
            title=f"🚨 {event_type}",
            body=f"{location} | {ts_str}",
            data={"event_type": event_type, "camera_id": camera_id}
        )

    logger.info(f"Security alert broadcast: {event_type} @ {location}")


def send_parking_receipt(
    user_email: str,
    user_phone: str,
    plate_number: str,
    entry_time: datetime,
    exit_time: datetime,
    duration_hours: float,
    fee: float,
    pdf_path: str = None
):
    """Send parking receipt via SMS and email after checkout."""
    ts_entry = entry_time.strftime("%H:%M, %d %b %Y")
    ts_exit = exit_time.strftime("%H:%M, %d %b %Y")
    sms_body = (
        f"✅ ParkPilot Receipt\n"
        f"Vehicle: {plate_number}\n"
        f"Entry: {ts_entry}\n"
        f"Exit: {ts_exit}\n"
        f"Duration: {duration_hours:.1f}h\n"
        f"Fee: ₹{fee:.2f}\n"
        f"Thank you!"
    )
    email_html = f"""
    <html><body style="font-family:Arial;background:#f0f4f8;padding:20px">
    <div style="max-width:500px;margin:auto;background:#fff;border-radius:12px;
                padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.1)">
        <div style="text-align:center;margin-bottom:20px">
            <h2 style="color:#2563eb">🚗 ParkPilot</h2>
            <p style="color:#64748b">Parking Receipt</p>
        </div>
        <table style="width:100%;border-collapse:collapse">
            <tr style="background:#f8fafc">
                <td style="padding:12px;color:#64748b">Vehicle</td>
                <td style="padding:12px;font-weight:bold">{plate_number}</td>
            </tr>
            <tr>
                <td style="padding:12px;color:#64748b">Entry Time</td>
                <td style="padding:12px">{ts_entry}</td>
            </tr>
            <tr style="background:#f8fafc">
                <td style="padding:12px;color:#64748b">Exit Time</td>
                <td style="padding:12px">{ts_exit}</td>
            </tr>
            <tr>
                <td style="padding:12px;color:#64748b">Duration</td>
                <td style="padding:12px">{duration_hours:.1f} hours</td>
            </tr>
            <tr style="background:#eff6ff">
                <td style="padding:12px;color:#1d4ed8;font-weight:bold">Total Fee</td>
                <td style="padding:12px;color:#1d4ed8;font-weight:bold;font-size:1.2em">
                    ₹{fee:.2f}
                </td>
            </tr>
        </table>
        <p style="text-align:center;color:#94a3b8;margin-top:20px;font-size:0.85em">
            ParkPilot Autonomous Parking System
        </p>
    </div></body></html>
    """
    if user_phone:
        send_sms(user_phone, sms_body)
    if user_email:
        send_email(
            user_email,
            f"ParkPilot Receipt — {plate_number}",
            email_html,
            attachment_path=pdf_path
        )
    logger.info(f"Receipt sent for {plate_number} | Fee: ₹{fee:.2f}")
