from django.contrib import admin

from apps.user.models import User, Address

admin.site.register(User)
admin.site.register(Address)
