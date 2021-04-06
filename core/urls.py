from django.urls import path
from . import views
urlpatterns = [
    path("post/", views.Post.as_view()),
    path("test/", views.Test.as_view()),

]
