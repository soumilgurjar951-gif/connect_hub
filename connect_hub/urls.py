"""
URL configuration for connect_hub project.
Hinglish: urls.py = Ghar ka main gate, yahan se decide hota hai kaunsa URL kahan jayega.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# health endpoint
from .health import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('api/', include('connect_hub.api_urls')),
    path('explore/', __import__('posts.views', fromlist=['explore_view']).explore_view, name='explore'),
    path('reels/', __import__('posts.views', fromlist=['reels_view']).reels_view, name='reels'),
    path('notifications/', __import__('connect_hub.api_views', fromlist=['notifications_page']).notifications_page, name='notifications'),
    path('', include('posts.urls')),
]

# Media files (avatar/post images) dev me serve karne ke liye
# Production me S3/R2 ya whitenoise se serve hoga
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
