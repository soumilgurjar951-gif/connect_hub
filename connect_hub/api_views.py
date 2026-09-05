"""
DRF API views for ConnectHub
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from accounts.models import Profile, Follow, Notification
from accounts.serializers import ProfileSerializer, UserSignupSerializer, FollowSerializer
from posts.models import Post, Like, Comment
from posts.serializers import PostSerializer, LikeSerializer, CommentSerializer, CommentCreateSerializer
from chat.models import Message
from chat.serializers import MessageSerializer
from rest_framework import serializers as drf_serializers

class NotificationSerializer(drf_serializers.ModelSerializer):
    actor_username = drf_serializers.CharField(source='actor.username', read_only=True)
    class Meta:
        model = Notification
        fields = ['id','actor','actor_username','type','post','is_read','created_at']

# --- Auth ---
class SignupAPI(generics.CreateAPIView):
    serializer_class = UserSignupSerializer
    permission_classes = [AllowAny]
    def create(self, request, *a, **kw):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        login(request, user)
        return Response({"id": user.id, "username": user.username}, status=201)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return Response({"ok": True, "username": user.username})
    return Response({"error": "Invalid credentials"}, status=400)

# --- Profile ---
class ProfileDetailAPI(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    lookup_field = 'username'
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_permissions(self):
        if self.request.method in ['PUT','PATCH']:
            return [IsAuthenticated()]
        return [AllowAny()]

class ProfileMeAPI(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

# --- Posts ---
class PostListCreateAPI(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        return Post.objects.filter(is_deleted=False).select_related('author').prefetch_related('images','likes').order_by('-created_at')
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class FeedAPI(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        following = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
        ids = list(following) + [self.request.user.id]
        return Post.objects.filter(author_id__in=ids, is_deleted=False).order_by('-created_at').select_related('author').prefetch_related('images','likes')

class PostDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticatedOrReadOnly]
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only author")
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

# --- Follow ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_toggle_api(request, username):
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(username__iexact=username)
        target = profile.user
    except:
        target = get_object_or_404(User, username__iexact=username)
    if target == request.user:
        return Response({"error": "Cannot follow yourself"}, status=400)
    obj, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        obj.delete()
        return Response({"is_following": False})
    # Notification
    if target != request.user:
        Notification.objects.create(recipient=target, actor=request.user, type='follow')
    return Response({"is_following": True})

# --- Like ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_toggle_api(request, pk):
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    obj, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        obj.delete()
        return Response({"is_liked": False, "likes_count": post.likes.count()})
    # Notification: like/reel_like
    if post.author != request.user:
        ntype = 'reel_like' if 'reels' in request.META.get('HTTP_REFERER','') else 'like'
        Notification.objects.create(recipient=post.author, actor=request.user, type=ntype, post=post)
    return Response({"is_liked": True, "likes_count": post.likes.count()})

# --- Comments ---
class CommentListCreateAPI(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['pk'], parent_comment__isnull=True).order_by('created_at').select_related('user').prefetch_related('replies')
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        if comment.post.author != self.request.user:
            Notification.objects.create(recipient=comment.post.author, actor=self.request.user, type='comment', post=comment.post)

def _resolve_user(username):
    """Profile.username ya User.username dono se dhoondho (slugified same hote hain)."""
    try:
        return Profile.objects.get(username__iexact=username).user
    except Profile.DoesNotExist:
        return get_object_or_404(User, username__iexact=username)


# --- User Search (nice-to-have: case-insensitive partial match) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_search_api(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 1:
        return Response([])
    profiles = Profile.objects.filter(username__icontains=q).exclude(user=request.user).select_related('user')[:10]
    return Response([{
        'username': p.username,
        'bio': (p.bio or '')[:60],
        'avatar': p.avatar.url if p.avatar else None,
        'followers_count': p.followers_count,
    } for p in profiles])


# --- Messages ---
class MessageListAPI(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    def get_other(self):
        return _resolve_user(self.kwargs['username'])
    def get_queryset(self):
        other = self.get_other()
        qs = Message.get_conversation(self.request.user, other)
        # Polling: ?after=<id> sirf naye messages
        after = self.request.GET.get('after')
        if after:
            try:
                qs = qs.filter(id__gt=int(after))
            except (ValueError, TypeError):
                pass
        return qs.order_by('created_at')[:100]
    def list(self, request, *args, **kwargs):
        # Thread kholte hi received ko read mark karo (Django view jaisa)
        resp = super().list(request, *args, **kwargs)
        try:
            other = self.get_other()
            Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)
        except Exception:
            pass
        return resp
    def perform_create(self, serializer):
        other = self.get_other()
        if other == self.request.user:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError("You cannot chat with yourself!")
        content = (serializer.validated_data.get('content') or '').strip()
        if not content:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError("Message cannot be empty!")
        if len(content) > 1000:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError("Max 1000 chars!")
        serializer.save(sender=self.request.user, receiver=other)

class ConversationListAPI(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    def _display_name(self, user):
        try:
            return user.profile.username
        except Exception:
            return user.username
    def list(self, request, *a, **kw):
        from django.db.models import Q
        msgs = Message.objects.filter(Q(sender=request.user)|Q(receiver=request.user)).order_by('-created_at').select_related('sender','receiver')
        seen = {}
        data = []
        for m in msgs:
            other = m.receiver if m.sender == request.user else m.sender
            if other.id not in seen:
                seen[other.id] = True
                avatar = None
                try:
                    if other.profile.avatar:
                        avatar = other.profile.avatar.url
                except Exception:
                    pass
                data.append({
                    "username": self._display_name(other),
                    "last_message": m.content[:40],
                    "created_at": m.created_at,
                    "unread": Message.objects.filter(sender=other, receiver=request.user, is_read=False).count(),
                    "avatar": avatar,
                    "last_id": m.id,
                })
        return Response(data)


class NotificationListAPI(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('actor','post').order_by('-created_at')[:50]

@login_required
def notifications_page(request):
    notifs = Notification.objects.filter(recipient=request.user).select_related('actor','post').order_by('-created_at')[:50]
    # mark as read when viewed? keep unread count for badge, but don't auto-mark; user can click
    return __import__('django.shortcuts', fromlist=['render']).render(request, 'notifications.html', {'notifications': notifs})
