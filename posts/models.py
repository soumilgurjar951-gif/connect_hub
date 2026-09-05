"""
posts/models.py - Post + PostImage + Like + Comment
Hinglish: Instagram ka post = text (500 char) + 1 se 4 images (soft delete)
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Post(models.Model):
    """
    Har post ka author ek User, content 500 char max, soft delete.
    Hinglish: is_deleted=True matlab user ko dikhna band, par DB me rahega (admin dekh sakta hai).
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'  # user.posts.all()
    )
    content = models.TextField(
        max_length=500,
        help_text="Max 500 characters"
    )
    location = models.CharField(max_length=100, blank=True, help_text="Optional location")
    tagged = models.CharField(max_length=200, blank=True, help_text="Comma @usernames")
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']  # Naya post sabse upar (reverse chronological)
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_deleted', '-created_at']),
        ]

    def __str__(self):
        # admin me "soumil: Hello world..." dikhega
        return f"{self.author.username}: {self.content[:30]}"


class PostImage(models.Model):
    """
    Har post pe 1-4 images, order se sequence.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='post_images/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['post', 'order']),
        ]

    def __str__(self):
        return f"Image {self.order} for Post {self.post_id}"


class Like(models.Model):
    """
    Toggle like - ek user ek post ko ek baar hi like kar sakta hai (unique).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_like')
        ]
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} likes Post {self.post_id}"


class Comment(models.Model):
    """
    1-level nested reply: comment ka parent_comment ho sakta hai (reply), par reply ka reply nahi.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="If replying, set parent comment"
    )
    content = models.TextField(max_length=200, help_text="Max 200 characters")
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional: edit/delete within 5 min ka logic views me check karenge, model me field nahi needed
    # Agar chaho to updated_at add kar sakte ho:
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']  # Purana comment pehle (thread jaisa)
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent_comment']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

    def clean(self):
        # 1-level nesting: parent ka parent nahi hona chahiye
        if self.parent_comment and self.parent_comment.parent_comment is not None:
            raise ValidationError("Only 1-level replies allowed (reply to a reply not allowed)!")
        # Reply same post ka hona chahiye
        if self.parent_comment and self.parent_comment.post_id != self.post_id:
            raise ValidationError("Reply must be on same post!")
