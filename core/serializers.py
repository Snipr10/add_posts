from rest_framework import serializers

from core.models import PostUrl, Proxy, Account, UserAgent, WorkCredentials


class PostSerializer(serializers.ModelSerializer):
    # db_post_url = serializers.CharField(max_length=150, required=False)
    # task_id = serializers.IntegerField(required=False)
    class Meta:
        model = PostUrl
        fields = (
            "db_post_url", "task_id"
        )


class ProxySerializer(serializers.ModelSerializer):
    host = serializers.CharField(max_length=255)
    port = serializers.IntegerField()
    login = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)
    available = serializers.BooleanField(default=True)
    last_time_checked = serializers.DateTimeField(required=False)
    attempts = serializers.IntegerField(default=0)
    expirationDate = serializers.DateTimeField()

    def create(self, validated_data):
        proxies = Proxy.objects.filter(host=validated_data['host'], port=validated_data['port'],
                                       login=validated_data['login'], password=validated_data['password'])
        if proxies.exists():
            return proxies.first()
        instance = Proxy.objects.create(**validated_data)
        return instance

    class Meta:
        model = Proxy
        fields = (
            "id", "host", "port", "login", "password", "available", "last_time_checked",
            "attempts", "expirationDate"
        )


class AccountSerializer(serializers.ModelSerializer):
    login = serializers.CharField(max_length=1024)
    password = serializers.CharField(max_length=1024)
    available = serializers.BooleanField(default=True)
    availability_check = serializers.DateTimeField(required=False)
    banned = serializers.BooleanField(default=True)

    class Meta:
        model = Account
        fields = (
            "id", "login", "password", "available", "availability_check", "banned"
        )


class WorkerSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    proxy = serializers.PrimaryKeyRelatedField(queryset=Proxy.objects.all())
    user_agent = serializers.PrimaryKeyRelatedField(queryset=UserAgent.objects.all(), default=None)

    def create(self, validated_data):
        user_agent = UserAgent.objects.filter(supported=True).order_by('?').first()
        # todo fix
        instance = None
        from add_posts.tasks import get_available_proxy
        proxy = get_available_proxy()
        if proxy is not None:
            instance = WorkCredentials.objects.create(user_agent=user_agent, account=validated_data["account"],
                                                      proxy=proxy)
            instance.account.available = True
            instance.account.banned = False
            instance.account.save()
            # not use this proxy in prod now
            instance.proxy.available = False
            instance.proxy.save()
        return instance

    class Meta:
        model = WorkCredentials
        fields = (
            "id", "account", "proxy", "user_agent", "inProgress", "in_progress_timestamp",
            "locked", "last_time_finished", "alive_timestamp"

        )
