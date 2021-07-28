import json

import requests
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from bs4 import BeautifulSoup

from add_posts.tasks import generate_proxy_session, check_facebook_url, check_proxy_available_for_facebook, \
    get_available_proxy
from core import serializers, models

# urllib3==1.25.11
from core.helpers import get_proxy, find_value


class Post(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.PostSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if models.PostUrl.objects.filter(db_post_url=serializer.initial_data['db_post_url']):
            return Response("url already exist", status=400)
        if not models.Task.objects.filter(id=int(serializer.initial_data['task_id'])).exists():
            return Response("Task not exist", status=400)
        serializer.save()
        return Response("ok")

    def get(self, request, *args, **kwargs):
        print('start')
        account_id = int(request.GET['id'])
        account = models.Account.objects.get(id=account_id)
        print('get proxy')

        proxy = get_available_proxy()
        email = account.login
        password = account.password
        session = generate_proxy_session(proxy.login, proxy.password, proxy.host, proxy.port)
        response = session.get('https://m.facebook.com', timeout=10)

        # login to Facebook
        response = session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        # If c_user cookie is present, login was successful
        print("check cookies")
        print(response.ok)
        if response.ok:
            print("c_user")
            if 'c_user' in response.cookies:
                start_page = session.get('https://www.facebook.com/')
                print(start_page.url)
                if 'checkpoint' not in start_page.url:
                    print("ok")
                    try:
                        W = models.WorkCredentials.objects.create(account=account, proxy=proxy, locked=False,
                                                                  user_agent=models.UserAgent.objects.filter(
                                                                      supported=True)
                                                                  .order_by('?').first()
                                                                  )
                        print(W.id)
                    except Exception:
                        print("cannot create WorkCredentials ")
            print(response.cookies)
        return Response(proxy.id)


class Proxy(generics.CreateAPIView, generics.UpdateAPIView, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ProxySerializer
    queryset = models.Proxy.objects.all()


class Account(generics.CreateAPIView, generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.AccountSerializer
    queryset = models.Account.objects.all()


class Worker(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.WorkerSerializer
    # queryset = models.Account.objects.all()


@csrf_exempt
@api_view(["GET"])
@permission_classes((AllowAny,))
def statistic(request):
    worker = models.WorkCredentials.objects.filter(locked=False).count()
    balance = requests.get('https://onlinesim.ru/api/getBalance.php?apikey=b8064527e750e01dd9d58e28507087e7')

    return Response({'proxy': models.Proxy.objects.filter(available=True, port=8080).count()
                              + worker,
                     'worker': worker,
                     'balance': float(balance.json()['balance'])},
                    status=status.HTTP_200_OK)
