from django.urls import re_path

from apps.search.views import SearchView

app_name = "search"
urlpatterns = [
    re_path(r'^$', SearchView.as_view(), name='search'),
]
