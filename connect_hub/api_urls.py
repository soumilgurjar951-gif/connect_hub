from django.urls import path
from . import api_views

urlpatterns = [
    path('signup/', api_views.SignupAPI.as_view(), name='api-signup'),
    path('login/', api_views.login_api, name='api-login'),
    path('profile/me/', api_views.ProfileMeAPI.as_view(), name='api-profile-me'),
    path('profile/<str:username>/', api_views.ProfileDetailAPI.as_view(), name='api-profile-detail'),
    path('posts/', api_views.PostListCreateAPI.as_view(), name='api-posts'),
    path('posts/<int:pk>/', api_views.PostDetailAPI.as_view(), name='api-post-detail'),
    path('feed/', api_views.FeedAPI.as_view(), name='api-feed'),
    path('posts/<int:pk>/like/', api_views.like_toggle_api, name='api-like'),
    path('posts/<int:pk>/comments/', api_views.CommentListCreateAPI.as_view(), name='api-comments'),
    path('follow/<str:username>/', api_views.follow_toggle_api, name='api-follow'),
    path('search/', api_views.user_search_api, name='api-search'),
    path('conversations/', api_views.ConversationListAPI.as_view(), name='api-conversations'),
    path('messages/<str:username>/', api_views.MessageListAPI.as_view(), name='api-messages'),
    path('notifications/', api_views.NotificationListAPI.as_view(), name='api-notifications'),
]
