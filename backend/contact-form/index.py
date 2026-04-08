import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from openai import OpenAI

def handler(event: dict, context) -> dict:
    """
    Обрабатывает заявку с формы обратной связи:
    1. Генерирует тёплый AI-ответ пользователю через OpenAI
    2. Отправляет письмо администратору с данными заявки
    3. Отправляет письмо пользователю с AI-ответом
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

    # Генерируем AI-ответ
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    ai_response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {
                'role': 'system',
                'content': (
                    'Ты — тёплый и внимательный специалист платформы поддержки АнтиБуллинг. '
                    'Твоя задача — ответить человеку, который написал нам сообщение. '
                    'Обращайся по имени, прояви искреннее сочувствие и понимание. '
                    'Сообщи, что его заявка принята и специалист свяжется с ним в течение 24 часов. '
                    'Напомни, что он не одинок и мы рядом. '
                    'Пиши по-русски, тепло, без канцеляризмов, 3-5 предложений.'
                )
            },
            {
                'role': 'user',
                'content': f'Имя: {name}\nСообщение: {message}'
            }
        ],
        max_tokens=300
    )
    ai_text = ai_response.choices[0].message.content.strip()

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
    <div style="font-family: sans-serif; max-width: 600px; padding: 24px;">
        <h2 style="color: #1275d8;">Новая заявка с сайта АнтиБуллинг</h2>
        <p><strong>Имя:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Сообщение:</strong></p>
        <blockquote style="border-left: 3px solid #1275d8; padding-left: 16px; color: #555;">{message}</blockquote>
        <hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;" />
        <p style="color: #888; font-size: 13px;">AI уже ответил пользователю автоматически.</p>
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
        <p>{ai_text}</p>
        <hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;" />
        <p style="color: #888; font-size: 13px;">Это автоматическое сообщение. Наш специалист свяжется с вами в течение 24 часов.</p>
    </div>
    """
    user_msg.attach(MIMEText(user_html, 'html'))

    with smtplib.SMTP_SSL(smtp_host, 465) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient, admin_msg.as_string())
        server.sendmail(smtp_user, email, user_msg.as_string())

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'success': True, 'ai_reply': ai_text})
    }
