import smtplib
from email.mime.text import MIMEText


def send_email(subject, body, to_email, login_email, password):
    """
    Wysyła wiadomość e-mail z tematem 'subject' i treścią 'body'
    na adres 'to_email', używając konta 'login_email' (hasło: 'password').
    Serwer: smtp.gmail.com:465
    """
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = login_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(login_email, password)
            server.send_message(msg)
    except Exception as e:
        print(f"[ERROR] Nie udało się wysłać e-maila: {e}")
