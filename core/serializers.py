from rest_framework import serializers

from core.models import PostUrl


class PostSerializer(serializers.ModelSerializer):
    # db_post_url = serializers.CharField(max_length=150, required=False)
    # task_id = serializers.IntegerField(required=False)
    class Meta:
        model = PostUrl
        fields = (
            "db_post_url", "task_id"
        )
