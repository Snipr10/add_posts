import requests
from django.utils import timezone
from rest_framework import generics, permissions

# Create your views here.
from rest_framework.response import Response
from bs4 import BeautifulSoup

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
        email = '79539510751'
        password = 'mnAFZqAFZn65747'
        session = requests.session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
        })
        proxy_login = 'usr10739536'
        proxy_password = 'usr10739536'
        proxy_host = '46.8.215.237'
        proxy_port = 4040
        proxy_str = f"{proxy_login}:{proxy_password}@{proxy_host}:{proxy_port}"
        print(proxy_str)
        proxies = {'http': f'http://{proxy_str}', 'https': f'https://{proxy_str}'}
        try:
            session.proxies.update(proxies)
            response = session.get('https://m.facebook.com', timeout=60)

            # login to Facebook
            response = session.post('https://m.facebook.com/login.php', data={
                'email': email,
                'pass': password
            }, allow_redirects=False)

            # If c_user cookie is present, login was successful
            print("check cookies")
            if 'c_user' in response.cookies:
                start_page = session.get('https://www.facebook.com/')
                return Response(start_page.url)

        except Exception as e:
            return Response(e)
        return Response("bad")


class Proxy(generics.CreateAPIView, generics.UpdateAPIView):
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
