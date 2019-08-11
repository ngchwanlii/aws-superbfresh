from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import View
# url: cart/add
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from apps.search.documents import GoodsSKUIndex


# url: /search/q?=<search_text>/page?sort
class SearchView(View):

    def get(self, request):

        q = request.GET.get('q', "")
        page = request.GET.get('page')
        try:
            ids = GoodsSKUIndex.search(q)
        except Exception as e:
            return render(request, 'search.html')

        skus = GoodsSKU.objects.filter(id__in=ids)
        # sort= default | price | hot
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = skus.order_by('price')
        elif sort == 'hot':
            skus = skus.order_by('-sales')
        else:
            sort = 'default'
            skus = skus.order_by('-id')

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

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_{user_id}'.format(user_id=user.id)
            cart_item_counts = map(int, conn.hvals(cart_key))
            cart_count = sum(cart_item_counts)

        context = {
            'query': q,
            'page': skus_page,
            'cart_count': cart_count,
            'sort': sort,
            'pages': pages,
        }

        return render(request, 'search.html', context)
