from django.urls import re_path

from apps.webhooks.views import StripeWebhookView

app_name = "webhooks"
urlpatterns = [
    re_path(r'^stripe$', StripeWebhookView.as_view(), name='stripe-hook'),
]
