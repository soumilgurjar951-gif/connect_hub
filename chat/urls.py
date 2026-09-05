from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list_view, name='conversation_list'),
    path('<str:username>/signal/', views.call_signal_view, name='call_signal'),
    path('<str:username>/ack/', views.call_ack_view, name='call_ack'),
    path('<str:username>/', views.chat_detail_view, name='chat_detail'),
]
