from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    class Meta:
        model = Message
        fields = ['id','sender','receiver','sender_username','receiver_username','content','image','is_read','created_at']
        # Hinglish: sender/receiver URL se aate hain (perform_create), body me bhejne ki zaroorat nahi — isliye read-only
        read_only_fields = ['sender','receiver','is_read','created_at']
