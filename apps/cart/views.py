from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin


# url: cart/add
class CartAddView(View):

    def post(self, request):
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login first!'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': 'Input fields incomplete'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': 'Product count invalid'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': 'SKU id does not exists'})

        # update / add num of items into cart (in Redis)
        conn = get_redis_connection('default')
        cart_key = "cart_{user_id}".format(user_id=user.id)
        sku_id_cart_count = conn.hget(cart_key, sku_id)
        if sku_id_cart_count:
            count += int(sku_id_cart_count)

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': 'Out of stock'})

        conn.hset(cart_key, sku_id, count)

        cart_item_counts = map(int, conn.hvals(cart_key))
        total_cart_count = sum(cart_item_counts)

        return JsonResponse({'res': 5, 'total_cart_count': total_cart_count, 'message': 'Added successfully'})


# urL: /cart
class CartInfoView(LoginRequiredMixin, View):

    def get(self, request):
        user = request.user

        conn = get_redis_connection('default')
        cart_key = "cart_{user_id}".format(user_id=user.id)
        # cart_dict = {'sku_id1': cart_count, 'sku_id2': cart_count, ...}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # amount = current sku's total_price
            sku.amount = sku.price * int(count)
            sku.count = int(count)
            skus.append(sku)

            total_price += sku.amount
            total_count += sku.count

        context = {
            'total_count': total_count,
            'total_price': total_price,
            'skus': skus
        }

        return render(request, 'cart.html', context)


# updated cart quantity & info
class CartUpdateView(View):

    def post(self, request):

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login first'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': 'Fields is invalid or incomplete'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': 'Invalid quantity'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': 'SKU product does not exists'})

        conn = get_redis_connection('default')
        cart_key = 'cart_{user_id}'.format(user_id=user.id)

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': 'Out of stock'})

        # update cart in Redis cart_key = {sku_id1: count, sku_id2: count, ....}
        conn.hset(cart_key, sku_id, count)

        # update total_cart count in cart page
        cart_item_counts = map(int, conn.hvals(cart_key))
        total_cart_count = sum(cart_item_counts)

        return JsonResponse({'res': 5, 'total_count': total_cart_count, 'message': 'Update successfully'})


# url: /cart/delete
class CartDeleteView(View):

    def post(self, request):

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login first'})

        sku_id = request.POST.get('sku_id')

        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': 'Invalid sku id'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': 'Invalid sku id'})

        conn = get_redis_connection('default')
        cart_key = 'cart_{user_id}'.format(user_id=user.id)

        # delete cart's specific sku_id record in Redis
        conn.hdel(cart_key, *[sku_id])
        cart_item_counts = map(int, conn.hvals(cart_key))
        total_cart_count = sum(cart_item_counts)

        return JsonResponse({'res': 3, 'total_count': total_cart_count, 'message': 'Delete successfully'})
