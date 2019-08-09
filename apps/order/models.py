from django.db import models

from db.base_model import BaseModel


class OrderInfo(BaseModel):
    PAYMENT_METHODS = {
        1: 'card',
    }

    PAYMENT_METHODS_CHOICES = (
        (1, 'card'),
    )

    PAYMENT_METHODS_ENUM = {
        'card': 1,
    }

    ORDER_STATUS_CHOICES = (
        (1, 'Pending payment'),
        (2, 'Shipping'),
        (3, 'Delivered'),
        (4, 'Pending comments'),
        (5, 'Completed')
    )

    ORDER_STATUS = {
        1: 'Pending payment',
        2: 'Shipping',
        3: 'Delivered',
        4: 'Pending comments',
        5: 'Completed'
    }

    ORDER_STATUS_ENUM = {
        'Pending payment': 1,
        'Shipping': 2,
        'Delivered': 3,
        'Pending comments': 4,
        'Completed': 5
    }

    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='order_id')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='user')
    addr = models.ForeignKey('user.Address', on_delete=models.CASCADE, verbose_name='addr')
    payment_method = models.SmallIntegerField(choices=PAYMENT_METHODS_CHOICES, default=3, verbose_name='payment_method')
    goods_total_count = models.IntegerField(default=1, verbose_name='goods_total_count')
    goods_total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='goods_total_price')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='order_status')
    transaction_num = models.CharField(max_length=128, default='', verbose_name='transaction_num')

    def __str__(self):
        return str(self.order_id)

    class Meta:
        db_table = 'sf_order_info'
        verbose_name = 'Order Info'
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    order = models.ForeignKey('OrderInfo', on_delete=models.CASCADE, verbose_name='order_info')
    sku = models.ForeignKey('goods.GoodsSKU', on_delete=models.CASCADE, verbose_name='sku')
    count = models.IntegerField(default=1, verbose_name='good_count')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='good_price')  # per good price
    comment = models.CharField(max_length=256, default='', verbose_name='good_comment')  # per good comment

    def __str__(self):
        return str(self.sku.id)

    class Meta:
        db_table = 'sf_order_goods'
        verbose_name = 'Order Goods'
        verbose_name_plural = verbose_name
