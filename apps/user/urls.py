from django.urls import re_path

from apps.user.views import RegisterView, LoginView, ActivateView

app_name = "user"

urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),
    re_path(r'^login$', LoginView.as_view(), name='login'),
    re_path(r'^active/(?P<token>.*)$', ActivateView.as_view(), name='activate'),
]
