from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods


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


# url: /goods/sku_id
class DetailView(View):

    def get(self, request, goods_id):

        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()

        # get goods comment
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # get latest goods sku
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:5]

        # get other similar goods by filtering this goods' SPU
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_{user_id}'.format(user_id=user.id)
            cart_item_counts = map(int, conn.hvals(cart_key))
            cart_count = sum(cart_item_counts)

            # add user's shopping browsing history
            conn = get_redis_connection('default')
            history_key = 'history_{user_id}'.format(user_id=user.id)
            # 1) first remove the duplicated goods_id if it exists
            conn.lrem(history_key, 0, goods_id)
            # 2) then update it to the "top" of the browsing stack
            conn.lpush(history_key, goods_id)
            # 3) store user's top 5 recent browsing/shopping history
            conn.ltrim(history_key, 0, 4)

        context = {'sku': sku, 'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'same_spu_skus': same_spu_skus,
                   'cart_count': cart_count}

        return render(request, 'detail.html', context)


# url: /list/type_id/page?sort
class ListView(View):

    def get(self, request, type_id, page):

        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()

        # sort= default | price | hot
        sort = request.GET.get('sort')

        goods = GoodsSKU.objects.filter(type=type)
        if sort == 'price':
            skus = goods.order_by('price')
        elif sort == 'hot':
            skus = goods.order_by('-sales')
        else:
            sort = 'default'
            skus = goods.order_by('-id')

        paginator = Paginator(skus, 20)

        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # get current page's skus object
        skus_page = paginator.page(page)

        # Control pagination number display logic, at most display '5 active pagination'
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:5]

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_{user_id}'.format(user_id=user.id)
            cart_item_counts = map(int, conn.hvals(cart_key))
            cart_count = sum(cart_item_counts)

        context = {'type': type, 'types': types,
                   'skus_page': skus_page,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'sort': sort}

        return render(request, 'list.html', context)
