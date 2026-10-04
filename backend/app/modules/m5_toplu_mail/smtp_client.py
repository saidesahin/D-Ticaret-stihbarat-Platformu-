"""
MODUL 5 - smtp_client.py

SMTP bilgisi girilmezse sistem crash etmez, "gonderilemedi - SMTP
yapilandirilmamis" hatasiyla doner (Modul 1-4'teki ayni guvenli desen).

ONEMLI - production notu: cok sayida mail atarken TEK istekte hepsini
gondermek hem sunucuyu kilitler hem spam-benzeri ani patlamaya sebep olur
(mail saglayicilari bunu tespit edip domaini/IP'yi kara listeye alabilir).
Gercek production'da bu islem Celery/Redis kuyruguna alinip yavas yavas
gonderilmeli. Bu ilk surumde basit/senkron gonderim var, `MAX_GONDERIM_PER_RUN`
ile kaba bir sinir koyduk (service.py icinde).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to_email: str, subject: str, html_body: str, from_name: str, from_email: str) -> tuple[bool, str | None]:
    """Basarili olursa (True, None), basarisiz olursa (False, hata_mesaji) doner."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return False, "SMTP yapilandirilmamis (.env icinde SMTP_HOST/SMTP_USER bos)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)
