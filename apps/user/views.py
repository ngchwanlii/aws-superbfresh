import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core import signing
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from apps.user.models import User, Address
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin


# URL: /user/register
class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):

        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        """ 
        Check if fields (username, password, email) is included
        If it is not, return an error message
        """
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': 'Fields incomplete'})

        """
        Check email format
        """
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': 'Invalid email address format'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': 'Please accept our terms & conditions'})

        """
        Check if user's email exists in database
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': 'User exists'})

        """
        Business logic processing
        """
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # send email activation link to new user
        token = signing.dumps({'confirm': user.id}, settings.SECRET_KEY, settings.SALT, compress=True)

        # send email asynchronously
        send_register_active_email.delay(email, username, token)

        return render(request, 'activate_pending.html')


class ActivateView(View):
    """ user account activation"""

    def get(self, request, token):

        try:
            # decrypt token from email activation link
            original_obj = signing.loads(token, settings.SECRET_KEY, settings.SALT,
                                         max_age=3600)  # activation link will expired in 1 hours
        except signing.BadSignature as err:
            # SignatureExpired is subclass of BadSignature
            # return error message
            return HttpResponse(err)

        # user's account is successfully activated
        user_id = original_obj.get('confirm')
        user = User.objects.get(id=user_id)
        user.is_active = 1
        user.save()

        # redirect to login page
        return redirect(reverse('user:login'))


# URL: /user/login
class LoginView(View):

    def get(self, request):

        username = ''
        checked = ''
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):

        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': 'Fields incomplete'})

        user = authenticate(username=username, password=password)
        if not user:
            return render(request, 'login.html', {'errmsg': 'Invalid email or password'})

        if not user.is_active:
            return render(request, 'login.html', {'errmsg': 'User account is not activate'})

        login(request, user)

        next_url = request.GET.get('next', reverse('goods:index'))

        response = redirect(next_url)

        if remember == 'on':
            response.set_cookie('username', username, max_age=7 * 24 * 3600)
        else:
            response.delete_cookie('username')

        return response


# /user/logout
class LogoutView(View):

    def get(self, request):
        # clear user's session + logout
        logout(request)

        return redirect(reverse('goods:index'))


# URL: /user
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)

        # get user's browsing history
        # bottom code is equal to -> StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        con = get_redis_connection('default')
        history_key = 'history_{user_id}'.format(user_id=user.id)
        sku_ids = con.lrange(history_key, 0, 4)
        goods_list = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            goods_list.append(goods)

        context = {
            'page': 'user',
            'address': address,
            'goods_list': goods_list
        }

        return render(request, 'user_center_info.html', context)


# URL: /user/order/<page>
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request, page, status=None):
        user = request.user
        orders_info = OrderInfo.objects.filter(user=user).order_by('-create_time')

        for order in orders_info:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            for order_sku in order_skus:
                amount = order_sku.count * order_sku.price
                order_sku.amount = amount

            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.order_skus = order_skus

        paginator = Paginator(orders_info, 5)

        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages or page <= 0:
            page = 1

        order_page = paginator.page(page)

        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order',
        }

        return render(request, 'user_center_order.html', context)


class AddressManager(models.Manager):

    def get_default_address(self, user):
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None

        return address


# URL: /user/address
class AddressView(LoginRequiredMixin, View):

    def get(self, request):

        user = request.user

        address = Address.objects.get_default_address(user)

        context = {
            'page': 'address',
            'address': address,
        }

        return render(request, 'user_center_address.html', context)

    def post(self, request):

        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        if not all([receiver, addr, zip_code, phone]):
            return render(request, 'user_center_address.html', {'errmsg': 'Fields incomplete'})

        # valid US phone number
        if not re.match(r'^\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})$', phone):
            return render(request, 'user_center_address.html', {'errmsg': 'Invalid phone number format'})

        user = request.user

        address = Address.objects.get_default_address(user)

        is_default = False if address else True

        # create new address
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default
                               )

        next_url = request.POST.get('next', reverse('user:address'))
        return redirect(next_url)
