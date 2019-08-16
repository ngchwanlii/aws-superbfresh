"""superbfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, re_path, path

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^tinymce/', include('tinymce.urls')),  # editor
    re_path(r'^user/', include('apps.user.urls', namespace='user')),  # user module
    re_path(r'^cart/', include('apps.cart.urls', namespace='cart')),  # cart module
    re_path(r'^order/', include('apps.order.urls', namespace='order')),  # order module
    re_path(r'^webhooks/', include('apps.webhooks.urls', namespace='webhooks')),  # webhooks module
    re_path(r'^search', include('apps.search.urls', namespace='es')),  # search module
    re_path('', include('apps.goods.urls', namespace='goods')),  # goods module
]
