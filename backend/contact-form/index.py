import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def handler(event: dict, context) -> dict:
    """
    Обрабатывает заявку с формы обратной связи:
    1. Отправляет письмо администратору с данными заявки
    2. Отправляет письмо пользователю с подтверждением
    """
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400',
            },
            'body': ''
        }

    body = json.loads(event.get('body', '{}'))
    name = body.get('name', '').strip()
    email = body.get('email', '').strip()
    message = body.get('message', '').strip()

    if not name or not email or not message:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Заполните все поля'})
        }

    smtp_host = os.environ['SMTP_HOST']
    smtp_user = os.environ['SMTP_USER']
    smtp_password = os.environ['SMTP_PASSWORD']
    recipient = os.environ['RECIPIENT_EMAIL']

    # Письмо администратору
    admin_msg = MIMEMultipart('alternative')
    admin_msg['Subject'] = f'Новая заявка с сайта — {name}'
    admin_msg['From'] = smtp_user
    admin_msg['To'] = recipient
    admin_html = f"""
    <div style="font-family: sans-serif; max-width: 600px; padding: 24px; background: #f9f9f9;">
        <h2 style="color: #1275d8; margin-bottom: 24px;">Новая заявка с сайта АнтиБуллинг</h2>
        <p><strong>Имя:</strong> {name}</p>
        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
        <p><strong>Сообщение:</strong></p>
        <blockquote style="border-left: 3px solid #1275d8; padding-left: 16px; color: #333; background: #fff; margin: 0; padding: 16px;">{message}</blockquote>
    </div>
    """
    admin_msg.attach(MIMEText(admin_html, 'html'))

    # Письмо пользователю
    user_msg = MIMEMultipart('alternative')
    user_msg['Subject'] = 'Мы получили ваше сообщение — АнтиБуллинг'
    user_msg['From'] = smtp_user
    user_msg['To'] = email
    user_html = f"""
    <div style="font-family: sans-serif; max-width: 600px; padding: 24px;">
        <h2 style="color: #1275d8;">АнтиБуллинг</h2>
        <p>Привет, {name}!</p>
        <p>Мы получили твоё сообщение и обязательно ответим в течение 24 часов. Ты не один — мы рядом.</p>
        <hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;" />
        <p style="color: #888; font-size: 13px;">Это автоматическое подтверждение получения заявки.</p>
    </div>
    """
    user_msg.attach(MIMEText(user_html, 'html'))

    with smtplib.SMTP_SSL(smtp_host, 465) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient, admin_msg.as_string())
        server.sendmail(smtp_user, email, user_msg.as_string())

    reply = f'Привет, {name}! Мы получили твоё сообщение и ответим в течение 24 часов. Ты не один — мы рядом.'

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'success': True, 'ai_reply': reply})
    }
