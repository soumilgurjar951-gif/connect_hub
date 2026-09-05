"""
accounts/models.py - Profile + Follow
Hinglish: Yahan user ka extra data rahega. Django ka User sirf username/email/password deta hai,
baaki bio/avatar/follow count hum yahan store karenge.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q, F


class Profile(models.Model):
    """
    Har User ka ek Profile - OneToOne matlab 1 user = 1 profile, duplicate nahi.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # User delete hua to Profile bhi delete
        related_name='profile'     # user.profile se access hoga
    )
    # Username unique + slugified -> "Soumil Gurjar" => "soumil-gurjar"
    # CharField max 30, unique
    username = models.CharField(
        max_length=30,
        unique=True,
        help_text="Unique username, 30 chars max, slugified (lowercase + hyphen)"
    )
    bio = models.TextField(
        max_length=150,
        blank=True,
        help_text="Max 150 characters"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile picture"
    )
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    # Onboarding
    interests = models.CharField(max_length=500, blank=True, help_text="Comma-separated e.g. Tech,Music")
    display_name = models.CharField(max_length=50, blank=True)
    onboarding_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"@{self.username} ({self.user.username})"  # admin me dikhega

    def save(self, *args, **kwargs):
        # Auto slugify username: "Soumil_Gurjar" -> "soumil-gurjar"
        if self.username:
            self.username = slugify(self.username)
        super().save(*args, **kwargs)


class Follow(models.Model):
    """
    Twitter-style follow - unidirectional (A follows B, B ko follow back zaroori nahi)
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',  # user.following.all() => jinhe ye follow karta hai
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',  # user.followers.all() => jo isko follow karte hain
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Ek user ek ko ek baar hi follow kar sakta hai
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow'),
            # Khud ko follow nahi kar sakta - database level pe rok
            models.CheckConstraint(
                condition=~Q(follower=F('following')),
                name='prevent_self_follow'
            ),
        ]
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username}"

    def clean(self):
        # Python level pe bhi check (admin/form me error dikhega)
        if self.follower_id == self.following_id:
            raise ValidationError("You cannot follow yourself!")


class Story(models.Model):
    """24h story — Instagram jaisa, image 1, 24h me expire"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to='stories/')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"Story by {self.user.username} at {self.created_at:%H:%M}"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)


class StoryView(models.Model):
    """Kaun kaun story dekha — owner tap karke dekh sakega"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'viewer')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.viewer.username} saw {self.story_id}"


class Notification(models.Model):
    """Like, follow, comment, reel like — sab ka notification"""
    TYPES = [('like','like'),('reel_like','reel_like'),('comment','comment'),('follow','follow'),('follow_request','follow_request')]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    type = models.CharField(max_length=15, choices=TYPES)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient','-created_at']), models.Index(fields=['recipient','is_read'])]

    def __str__(self):
        return f"{self.actor} -> {self.recipient} {self.type}"
