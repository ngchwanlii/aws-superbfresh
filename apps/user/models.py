from django.contrib.auth.models import AbstractUser
from django.db import models

from db.base_model import BaseModel


class User(AbstractUser, BaseModel):
    class Meta:
        db_table = 'sf_user'
        verbose_name = 'User'
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    def get_default_address(self, user):
        '''get user default address'''
        try:
            address = self.get(user=user, is_default=True)  # models.Manager
        except self.model.DoesNotExist:
            address = None

        return address


class Address(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='user')
    receiver = models.CharField(max_length=20, verbose_name='receiver')
    addr = models.CharField(max_length=256, verbose_name='address')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='zip_code')
    phone = models.CharField(max_length=11, verbose_name='phone')
    is_default = models.BooleanField(default=False, verbose_name='is_default')

    objects = AddressManager()

    class Meta:
        db_table = 'sf_address'
        verbose_name = 'Address'
        verbose_name_plural = verbose_name
