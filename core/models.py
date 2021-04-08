from django.db import models


class PostUrl(models.Model):
    db_post_url = models.CharField(max_length=100)
    task_id = models.IntegerField()
    is_ready = models.BooleanField(default=False)
    is_successful = models.BooleanField(default=True)
    is_parsing = models.BooleanField(default=False)
    added_date = models.DateField(auto_now=True)

    class Meta:
        db_table = 'post_url'


class Content(models.Model):
    text = models.CharField(max_length=4096, null=True, blank=True)

    class Meta:
        db_table = 'content'


class PostStat(models.Model):
    likes = models.CharField(max_length=32, null=True, blank=True)
    comments = models.CharField(max_length=32, null=True, blank=True)
    shares = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = 'post_stat'


class Task(models.Model):
    interval = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tasks'


class User(models.Model):
    name = models.CharField(max_length=1024, null=True, blank=True)
    link = models.CharField(max_length=1024, null=True, blank=True)
    sex = models.CharField(max_length=8, null=True, blank=True)
    city_of_birth = models.CharField(max_length=128, null=True, blank=True)
    current_city = models.CharField(max_length=128, null=True, blank=True)
    birthday = models.CharField(max_length=128, null=True, blank=True)
    fb_id = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = 'users'


class Post(models.Model):
    date = models.DateField(auto_now=True)
    last_time_updated = models.DateField(auto_now=True)
    fb_post_id = models.CharField(max_length=1024, null=True, blank=True)
    fb_repost_id = models.CharField(max_length=128, null=True, blank=True)
    fb_repost_link = models.CharField(max_length=2048, null=True, blank=True)
    fb_post_link = models.CharField(max_length=1024, null=True, blank=True)
    fb_post_link_likes = models.CharField(max_length=1024, null=True, blank=True)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(PostStat, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'posts'


class Proxy(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    login = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    available = models.BooleanField(default=True)
    last_time_checked = models.DateTimeField(auto_now=True)
    attempts = models.IntegerField(default=0)
    expirationDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proxy'
