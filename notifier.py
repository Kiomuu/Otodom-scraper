import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, to_email, login_email, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = login_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(login_email, password)
        server.send_message(msg)