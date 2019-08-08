from django.core.cache import cache
from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


class IndexView(View):

    def get(self, request):

        context = cache.get('home_index_page_data')

        if context is None:

            types = GoodsType.objects.all()

            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # GoodsType
            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners,
                       }

            # page caching expired after 1 hours
            cache.set('home_index_page_data', context, 3600)

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_{user_id}'.format(user_id=user.id)
            cart_item_counts = map(int, conn.hvals(cart_key))
            cart_count = sum(cart_item_counts)

        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)
