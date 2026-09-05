from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('posts/create/', views.post_create_view, name='create'),
    path('posts/<int:pk>/', views.post_detail_view, name='detail'),
    path('posts/<int:pk>/delete/', views.post_delete_view, name='delete'),
    path('posts/<int:pk>/like/', views.like_toggle_view, name='like_toggle'),
    path('posts/<int:pk>/comment/', views.comment_create_view, name='comment_create'),
    path('comments/<int:pk>/edit/', views.comment_edit_view, name='comment_edit'),
    path('comments/<int:pk>/delete/', views.comment_delete_view, name='comment_delete'),
    path('feed/', views.feed_view, name='feed_alt'),
]
