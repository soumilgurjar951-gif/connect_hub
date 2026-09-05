from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Profile, Follow

class ProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Profile
        fields = ['id','user','user_username','username','bio','avatar','followers_count','following_count','created_at']
        read_only_fields = ['followers_count','following_count','created_at']

class UserSignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    bio = serializers.CharField(max_length=150, required=False, allow_blank=True)
    def validate_username(self, v):
        slug = slugify(v)
        if len(slug) < 3: raise serializers.ValidationError("Min 3 chars")
        if User.objects.filter(username__iexact=slug).exists(): raise serializers.ValidationError("Taken")
        if Profile.objects.filter(username__iexact=slug).exists(): raise serializers.ValidationError("Taken")
        return slug
    def validate_email(self, v):
        if User.objects.filter(email__iexact=v.lower()).exists(): raise serializers.ValidationError("Email taken")
        return v.lower()
    def create(self, validated):
        user = User.objects.create_user(username=validated['username'], email=validated['email'], password=validated['password'])
        Profile.objects.create(user=user, username=validated['username'], bio=validated.get('bio',''))
        return user

class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    class Meta:
        model = Follow
        fields = ['id','follower','following','follower_username','following_username','created_at']
        read_only_fields = ['follower','created_at']
