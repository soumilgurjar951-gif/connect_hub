from django.contrib import admin
from .models import Message, CallSignal


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_snippet', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('created_at',)

    def content_snippet(self, obj):
        return obj.content[:40]
    content_snippet.short_description = 'Content'


@admin.register(CallSignal)
class CallSignalAdmin(admin.ModelAdmin):
    list_display = ('caller', 'receiver', 'type', 'is_video', 'is_read', 'created_at')
    list_filter = ('type', 'is_video', 'is_read')
