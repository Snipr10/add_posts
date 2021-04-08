from django.urls import path
from . import views
urlpatterns = [
    path("post/", views.Post.as_view()),
    path("test/", views.Test.as_view()),
    path("get_task/", views.Task.as_view()),

]
