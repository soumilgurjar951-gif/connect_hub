from django.urls import path
from . import views, onboarding_views, settings_views, story_views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/1/', onboarding_views.step1, name='onboarding_step1'),
    path('onboarding/2/', onboarding_views.step2, name='onboarding_step2'),
    path('onboarding/3/', onboarding_views.step3, name='onboarding_step3'),
    path('settings/', settings_views.settings_view, name='settings'),
    path('story/create/', story_views.story_create_view, name='story_create'),
    path('story/<int:pk>/', story_views.story_view, name='story_detail'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('suggested/', views.suggested_view, name='suggested'),
    path('profile/<str:username>/followers/', views.followers_list_view, name='followers'),
    path('profile/<str:username>/following/', views.following_list_view, name='following'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('follow/<str:username>/', views.follow_toggle_view, name='follow_toggle'),
]
