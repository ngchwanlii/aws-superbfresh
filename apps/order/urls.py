from django.urls import re_path

from apps.order.views import OrderPlaceView, OrderCommitView, OrderPayView, OrderCommentView

app_name = "order"
urlpatterns = [
    re_path(r'^place$', OrderPlaceView.as_view(), name='place'),  # display order page
    re_path(r'^commit$', OrderCommitView.as_view(), name='commit'),  # create order
    re_path(r'^pay$', OrderPayView.as_view(), name='pay'),  # pay order
    re_path(r'^comment/(?P<order_id>.+)$', OrderCommentView.as_view(), name='comment'),  # order comment
]
