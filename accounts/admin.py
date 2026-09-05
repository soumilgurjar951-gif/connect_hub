from django.contrib import admin
from .models import Profile, Follow, Story, StoryView, Notification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'followers_count', 'following_count', 'created_at')
    search_fields = ('username', 'user__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    list_filter = ('created_at',)

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    list_filter = ('created_at',)

@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('story', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient','actor','type','post','is_read','created_at')
    list_filter = ('type','is_read')
