from django.urls import re_path

from apps.user.views import RegisterView, ActivateView, LoginView, LogoutView, UserInfoView, UserOrderView, AddressView

app_name = "user"
urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),
    re_path(r'^login$', LoginView.as_view(), name='login'),
    re_path(r'^logout$', LogoutView.as_view(), name='logout'),
    re_path(r'^active/(?P<token>.*)$', ActivateView.as_view(), name='activate'),

    re_path(r'^address$', AddressView.as_view(), name='address'),
    re_path(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    re_path(r'^order/(?P<page>\d+)/(?P<status>\w+)$', UserOrderView.as_view(), name='order'),
    re_path(r'^$', UserInfoView.as_view(), name='user'),
]
