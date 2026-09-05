"""
chat/models.py - Direct Message (1-to-1)
Hinglish: WhatsApp jaisa, par sirf 1-to-1 (group nahi). Polling se kaam chalega, WebSocket baad me.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class Message(models.Model):
    """
    Sender -> Receiver, text 1000 char, is_read flag.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'  # user.sent_messages.all()
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'  # user.received_messages.all()
    )
    content = models.TextField(max_length=1000, blank=True, help_text="Max 1000 characters")
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # Conversation me purana pehle
        indexes = [
            models.Index(fields=['sender', 'receiver', 'created_at']),
            models.Index(fields=['receiver', 'is_read']),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:20]}"

    @classmethod
    def get_conversation(cls, user1, user2):
        """Do users ke beech ke saare messages (dono direction)"""
        return cls.objects.filter(
            Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)
        ).order_by('created_at')


class CallSignal(models.Model):
    """WebRTC signaling — offer/answer/ice + hangup, polling se exchange"""
    CALL_TYPES = [('offer','offer'),('answer','answer'),('ice','ice'),('hangup','hangup')]
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_made')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_received')
    type = models.CharField(max_length=10, choices=CALL_TYPES)
    data = models.TextField(blank=True)  # JSON string (SDP or ICE)
    is_video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['receiver','is_read','created_at'])]

    def __str__(self):
        return f"{self.caller} -> {self.receiver} {self.type} {'video' if self.is_video else 'audio'}"
