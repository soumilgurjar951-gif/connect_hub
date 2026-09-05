from rest_framework import serializers
from .models import Post, PostImage, Like, Comment

class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id','image','order']

class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    replies = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id','user','user_username','post','parent_comment','content','created_at','updated_at','replies']
        read_only_fields = ['user','created_at','updated_at']
    def get_replies(self, obj):
        if obj.parent_comment is None:
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True).data
        return []

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = ['id','author','author_username','content','is_deleted','created_at','images','likes_count','comments_count','is_liked']
        read_only_fields = ['author','is_deleted','created_at']
    def get_is_liked(self, obj):
        req = self.context.get('request')
        if req and req.user.is_authenticated:
            return obj.likes.filter(user=req.user).exists()
        return False

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id','user','post','created_at']
        read_only_fields = ['user','created_at']

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id','post','parent_comment','content']
        read_only_fields = ['id']
    def validate(self, attrs):
        parent = attrs.get('parent_comment')
        if parent and parent.parent_comment is not None:
            raise serializers.ValidationError("Only 1-level replies allowed")
        if parent and parent.post != attrs['post']:
            raise serializers.ValidationError("Parent must be same post")
        return attrs
