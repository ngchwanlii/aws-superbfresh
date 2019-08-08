from django.urls import re_path

from apps.goods.views import IndexView, DetailView, ListView

app_name = "goods"

urlpatterns = [
    # NOTE:
    # - If user visit /, return a 'static' index.html from Nginx
    # - If user visit /index, the index.html return from Django server
    re_path(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
    re_path(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),
    re_path(r'index', IndexView.as_view(), name='index'),
]
