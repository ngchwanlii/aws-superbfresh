# Init for Redis remote-server
import os
import smtplib
from email.mime.text import MIMEText

import django
from celery import Celery
from django.conf import settings
from django.template import loader

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'superbfresh.settings')
django.setup()

# import apps' model should be written after django.setup()!
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# Celery
app = Celery('celery_tasks.tasks', broker=settings.REDIS_BROKER_LOCATION)


@app.task
def send_register_active_email(to_email, username, token):
    activate_url = "{SCHEME}://{HOST}/user/active/{token}".format(SCHEME=settings.BASE_SCHEME,
                                                                  HOST=settings.BASE_HOST,
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


@app.task
def generate_static_index_html():
    # goods types
    types = GoodsType.objects.all()

    # goods home page banners
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # obtain goods' types=categories image banners / title tag
    for type in types:  # GoodsType
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        type.image_banners = image_banners
        type.title_banners = title_banners

    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners,
               'cart_count': 0,
               }

    template = loader.get_template('static_index.html')
    static_index_html = template.render(context)

    # generate static index html
    index_html_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(index_html_path, 'w') as f:
        f.write(static_index_html)
