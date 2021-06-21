import json

import requests
from django.utils import timezone
from rest_framework import generics, permissions

# Create your views here.
from rest_framework.response import Response
from bs4 import BeautifulSoup

from add_posts.tasks import generate_proxy_session, check_facebook_url, check_proxy_available_for_facebook
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
        from add_posts.tasks import get_available_proxy
        key = 'd73007770373106ac0256675c604bc22'
        new_proxy = requests.get("https://api.best-proxies.ru/proxylist.json?key=%s&twitter=1&type=http&speed=1" % key,
                                 timeout=60)
        for proxy in json.loads(new_proxy.text):
            host = proxy['ip']
            port = proxy['port']
            session = generate_proxy_session('test', 'test', host, port)
            if check_facebook_url(session):
                s = check_proxy_available_for_facebook(session)
                print(s)


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


