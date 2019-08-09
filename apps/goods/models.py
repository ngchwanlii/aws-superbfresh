from django.db import models
from tinymce.models import HTMLField

from db.base_model import BaseModel


class GoodsType(BaseModel):
    name = models.CharField(max_length=20, verbose_name='name')
    logo = models.CharField(max_length=20, verbose_name='logo')
    image = models.ImageField(upload_to='type', verbose_name='image')

    class Meta:
        db_table = 'sf_goods_type'
        verbose_name = 'Goods Types'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSKU(BaseModel):
    status_choices = (
        (0, 'offline'),
        (1, 'online'),
    )

    type = models.ForeignKey('GoodsType', on_delete=models.CASCADE, verbose_name='type')
    goods = models.ForeignKey('Goods', on_delete=models.CASCADE, verbose_name='spu')
    name = models.CharField(max_length=20, verbose_name='name')
    desc = models.CharField(max_length=256, verbose_name='desc')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='price')
    unit = models.CharField(max_length=20, verbose_name='unit')
    image = models.ImageField(upload_to='goods', verbose_name='image')
    stock = models.IntegerField(default=1, verbose_name='stock')
    sales = models.IntegerField(default=0, verbose_name='sales')
    status = models.SmallIntegerField(default=1, choices=status_choices, verbose_name='status')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sf_goods_sku'
        verbose_name = 'Goods SKU'
        verbose_name_plural = verbose_name


# Goods' SPU
class Goods(BaseModel):
    name = models.CharField(max_length=20, verbose_name='spu_name')
    detail = HTMLField(blank=True, verbose_name='details')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sf_goods'
        verbose_name = 'Goods SPU'
        verbose_name_plural = verbose_name


class GoodsImage(BaseModel):
    sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='sku')
    image = models.ImageField(upload_to='goods', verbose_name='image')

    def __str__(self):
        return str(self.sku.id)

    class Meta:
        db_table = 'sf_goods_image'
        verbose_name = 'Goods Image'
        verbose_name_plural = verbose_name


class IndexGoodsBanner(BaseModel):
    sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='sku')
    image = models.ImageField(upload_to='banner', verbose_name='image')
    index = models.SmallIntegerField(default=0, verbose_name='banner_index_order')  # show banners in order: [0 1 2 3]

    def __str__(self):
        return str(self.sku.id)

    class Meta:
        db_table = 'sf_index_banner'
        verbose_name = 'Home Banner'
        verbose_name_plural = verbose_name


# Display on homepage's body - Goods Categories, listed as item
class IndexTypeGoodsBanner(BaseModel):
    DISPLAY_TYPE_CHOICES = (
        (0, "tag"),
        (1, "image")
    )

    type = models.ForeignKey('GoodsType', on_delete=models.CASCADE, verbose_name='type')
    sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='sku')
    display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='display_type')
    index = models.SmallIntegerField(default=0, verbose_name='banner_index_order')

    def __str__(self):
        return str(self.sku.name)

    class Meta:
        db_table = 'sf_index_type_goods'
        verbose_name = "Home Category List Banner"
        verbose_name_plural = verbose_name


# Promotion Banner: Display on side of the slide in homepage
class IndexPromotionBanner(BaseModel):
    name = models.CharField(max_length=20, verbose_name='promotion_name')
    url = models.CharField(max_length=256, verbose_name='promotion_url')
    image = models.ImageField(upload_to='banner', verbose_name='promotion_image')
    index = models.SmallIntegerField(default=0, verbose_name='promotion_index_order')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sf_index_promotion'
        verbose_name = "Home Promotion"
        verbose_name_plural = verbose_name
