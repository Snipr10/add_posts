from django.urls import path
from . import views
urlpatterns = [
    path("post/", views.Post.as_view()),

    path("proxy/", views.Proxy.as_view()),
    path("proxy/<int:pk>/", views.Proxy.as_view()),

    path("account/", views.Account.as_view()),
    path("account/<int:pk>/", views.Account.as_view()),

    path("worker/", views.Worker.as_view()),

    path("worker/", views.Post.as_view()),


]
