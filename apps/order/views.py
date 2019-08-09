from datetime import datetime

import stripe
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from apps.user.models import Address
from utils.converter import to_cents
from utils.mixin import LoginRequiredMixin


# url: /order/place
class OrderPlaceView(LoginRequiredMixin, View):
    """ Display Order page after customer submit from cart page"""

    def post(self, request):
        user = request.user
        sku_ids = request.POST.getlist('sku_ids')  # [1,26]

        if not sku_ids:
            return redirect(reverse('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_{user_id}'.format(user_id=user.id)

        skus = []
        total_count = 0
        total_price = 0

        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)
            try:
                count = int(count)
            except Exception:
                count = 0

            amount = sku.price * count

            sku.count = count
            sku.amount = amount
            skus.append(sku)

            total_count += count
            total_price += amount

        addrs = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price,
                   'addrs': addrs,
                   'sku_ids': sku_ids}

        return render(request, 'place_order.html', context)


# url: /order/commit
class OrderCommitView(View):

    @transaction.atomic
    def post(self, request):

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login first'})

        addr_id = request.POST.get('addr_id')
        pay_method = int(request.POST.get('pay_method'))
        sku_ids = request.POST.get('sku_ids')  # sku_ids = 1,3,5,16....

        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': 'Fields invalid or incomplete'})

        if pay_method not in OrderInfo.PAYMENT_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': 'Invalid payment method'})

        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': 'Invalid address'})

        # Implement create order service
        # Create order_info 1st, then order_goods because there's order_info_id foreign key in order_goods
        # Ex: order_id = 20190722160830+user.id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # goods total_count & total price
        total_count = 0
        total_price = 0

        # Setup savepoints
        save_id = transaction.savepoint()

        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             payment_method=pay_method,
                                             goods_total_count=total_count,
                                             goods_total_price=total_price,
                                             )

            # For any sku items in user's cart,
            # we need to create each sku order_gooods model & record it
            conn = get_redis_connection('default')
            cart_key = 'cart_{user_id}'.format(user_id=user.id)

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    # MySQL syntax: select * from sf_goods_sku where id=sku_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': 'SKU id does not exists'})

                count = conn.hget(cart_key, sku_id)
                count = int(count)

                # Verify whether intend to purchase item's sku quantity exceed item's sku stock or not,
                # if it is rollback to save point
                if count > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 5, 'errmsg': 'Out of stock'})

                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # Update GoodsSKU stock & sales
                sku.stock -= count
                sku.sales += count
                sku.save()

                # Update / accumulate order item's count and amount to total_count & total_price
                amount = sku.price * count
                total_count += count
                total_price += amount

            order.goods_total_count = total_count
            order.goods_total_price = total_price
            order.save()

        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 6, 'errmsg': 'You already added this order in your order page'})

        # After purchased all the selected goods from cart, we need to remove these goods'
        # sku id from Redis with key = cart_user.id
        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key, *sku_ids)
        return JsonResponse({'res': 7, 'message': 'Checkout successfully!'})


# url: /order/pay
class OrderPayView(View):

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login first'})

        # orders = json.loads(request.POST.get('orders'))
        order_id = request.POST.get('order_id')
        page = request.POST.get('page')

        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': 'Invalid order id'})

        try:
            orders_info = OrderInfo.objects.get(order_id=order_id,
                                                user=user,
                                                payment_method=1,
                                                order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': 'Invalid order'})

        try:
            order_goods = OrderGoods.objects.filter(order_id=order_id)
        except OrderGoods.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': 'Invalid order'})

        stripe.api_key = settings.STRIPE_API_KEY
        # stripe amout is in smallest unit = cents
        # Ex: 100 = $1.00, and must be in int format
        line_items = []
        for order_good in order_goods:
            line_items.append({
                "name": order_good.sku.name,
                "description": order_good.sku.desc,
                'amount': to_cents(order_good.price),
                "currency": "usd",
                "quantity": order_good.count,
            })

        session = stripe.checkout.Session.create(
            success_url="{BASE_SCHEME}://{BASE_HOST}:{BASE_PORT}/user/order/{PAGE}/{STATUS}".format(
                BASE_SCHEME=settings.BASE_SCHEME,
                BASE_HOST=settings.BASE_HOST,
                BASE_PORT=settings.BASE_PORT,
                PAGE=page,
                STATUS="success"),
            cancel_url="{BASE_SCHEME}://{BASE_HOST}:{BASE_PORT}/user/order/{PAGE}/{STATUS}".format(
                BASE_SCHEME=settings.BASE_SCHEME,
                BASE_HOST=settings.BASE_HOST,
                BASE_PORT=settings.BASE_PORT,
                PAGE=page,
                STATUS="cancel"),
            payment_method_types=["card"],
            customer_email=user.email,
            client_reference_id=order_id,
            line_items=line_items
        )

        return JsonResponse({'res': 3, 'sessionId': session.id})


class OrderCommentView(LoginRequiredMixin, View):

    def get(self, request, order_id):

        user = request.user

        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            amount = order_sku.count * order_sku.price
            order_sku.amount = amount

        order.order_skus = order_skus

        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):

        user = request.user
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        for i in range(1, total_count + 1):
            sku_id = request.POST.get("sku_{i}".format(i=i))  # sku_1 sku_2
            # comment's content
            content = request.POST.get('content_{i}'.format(i=i), '')  # content_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        # order completed after giving a comment
        order.order_status = 5  # order's status = completed
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
