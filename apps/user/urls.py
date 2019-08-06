from django.urls import re_path

from apps.user.views import RegisterView, LoginView

app_name = "user"

urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),
    re_path(r'^login$', LoginView.as_view(), name='login'),
]