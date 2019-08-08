# Init for Redis remote-server
import os
import smtplib
from email.mime.text import MIMEText

import django
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superbfresh.settings')
django.setup()

# import apps' model should be written after django.setup()!

# Celery
app = Celery('celery_tasks.tasks', broker=settings.REDIS_BROKER_LOCATION)


@app.task
def send_register_active_email(to_email, username, token):
    activate_url = "{SCHEME}://{HOST}:{PORT}/user/active/{token}".format(SCHEME=settings.BASE_SCHEME,
                                                                         HOST=settings.BASE_HOST,
                                                                         PORT=settings.BASE_PORT,
                                                                         token=token)

    html_message = """\
    <html>
        <head></head>
        <body>
            <p>Welcome {username},</p>
            <p>Please click the following link to activate your account: </p>
            <a href="{url}">{url}</a>
        </body>
    </html>
    """.format(username=username, url=activate_url)

    msg = MIMEText(html_message, "html")
    msg['Subject'] = 'Welcome to SuperbFresh'
    msg['From'] = settings.EMAIL_HOST_USER
    msg['To'] = to_email

    with smtplib.SMTP(settings.AWS_SES_REGION_ENDPOINT) as s:
        s.connect(settings.AWS_SES_REGION_ENDPOINT, settings.AWS_SES_EMAIL_PORT)
        s.starttls()
        s.login(settings.AWS_SES_ACCESS_KEY_ID, settings.AWS_SES_SECRET_ACCESS_KEY)
        s.send_message(msg)
        s.quit()
