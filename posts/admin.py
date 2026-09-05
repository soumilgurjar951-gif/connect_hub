from django.contrib import admin
from .models import Post, PostImage, Like, Comment


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content_snippet', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('content', 'author__username')
    inlines = [PostImageInline]
    readonly_fields = ('created_at',)

    def content_snippet(self, obj):
        return obj.content[:50]
    content_snippet.short_description = 'Content'


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'order', 'image')
    list_filter = ('order',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'parent_comment', 'content_snippet', 'created_at')
    search_fields = ('content', 'user__username')
    list_filter = ('created_at',)

    def content_snippet(self, obj):
        return obj.content[:40]
    content_snippet.short_description = 'Content'
