import json

import requests
from django.utils import timezone
from rest_framework import generics, permissions

# Create your views here.
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
        account_id = request.GET['id']
        # proxy = get_available_proxy()
        return Response(account_id)

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


