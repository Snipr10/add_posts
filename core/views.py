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
        serializer.save()
        return Response("ok")


class Test(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        from add_posts.tasks import start_parsing_url
        start_parsing_url()
        return Response("ok")


class Task(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            models.Task.objects.get(id=6008)
            return Response("ok")
        except Exception as e:
            return Response(e)


