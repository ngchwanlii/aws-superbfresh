import re

from django.conf import settings
from django.contrib.auth import login, authenticate
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic.base import View

from apps.user.models import User
from celery_tasks.tasks import send_register_active_email


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
            return render(request, 'register.html', {'errmsg': 'Username exists'})

        """
        Business logic processing
        """
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # send email activation link to new user
        token = signing.dumps({'confirm': user.id}, settings.SECRET_KEY, settings.SALT, compress=True)

        # # send email asynchronously
        send_register_active_email.delay(email, username, token)

        return redirect(reverse('goods:index'))


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
