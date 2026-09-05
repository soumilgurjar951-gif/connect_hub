"""
posts/views.py - Feed + Post CRUD + Like/Comment
Hinglish: Like = toggle, Comment = 1-level reply, 5 min me edit/delete
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .models import Post, PostImage, Like, Comment
from .forms import PostCreateForm, CommentForm
from accounts.models import Follow


@login_required
def explore_view(request):
    from accounts.models import Profile
    q = request.GET.get('q','').strip()
    tag = request.GET.get('tag','').strip()
    tag = tag if tag in ["For You","Tech","Music","Sports","Art","Gaming","Food"] else "For You"
    qs = Post.objects.filter(is_deleted=False).select_related('author').prefetch_related('images','likes','comments').order_by('-created_at')
    if q:
        # search people or content
        qs = qs.filter(content__icontains=q) | Post.objects.filter(author__profile__username__icontains=q, is_deleted=False).select_related('author').prefetch_related('images')
        qs = qs.distinct()
    # fake tag filter: if tag != For You, filter by content contains tag keyword (MVP)
    if tag != "For You":
        qs = qs.filter(content__icontains=tag)
    paginator = Paginator(qs, 18)
    page_obj = paginator.get_page(request.GET.get('page',1))
    # Trending for Explore
    import re
    from collections import Counter
    recent = Post.objects.filter(is_deleted=False).order_by('-created_at')[:50]
    tags = []
    for p in recent:
        tags.extend(re.findall(r"#(\w+)", p.content))
    trending = Counter([t.lower() for t in tags]).most_common(5)
    if not trending:
        trending = [('buildinpublic', 24), ('photography', 18), ('indie', 12)]
    # ID search: username match (exact id search)
    from accounts.models import Profile
    user_results = []
    if q:
        user_results = Profile.objects.filter(username__icontains=q).select_related('user')[:8]
    return render(request, 'explore.html', {
        "posts": page_obj.object_list,
        "page_obj": page_obj,
        "q": q,
        "tags": ["For You","Tech","Music","Sports","Art","Gaming","Food"],
        "active_tag": tag,
        "trending": trending,
        "user_results": user_results,
    })

@login_required
def reels_view(request):
    """Reels ka alag panel — any reel (kisi bhi user ki), shuffle + most liked mix — login ke baad hi"""
    from django.db.models import Count
    # Any reel: sabhi posts me se — shuffle + most liked mix (har baar alag)
    # Hinglish: ?sort=liked se most liked first, warna random
    sort = request.GET.get('sort','shuffle')
    base = Post.objects.filter(is_deleted=False).select_related('author').prefetch_related('images','likes','comments')
    if sort == 'liked':
        qs = base.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
    else:
        qs = base.order_by('?')  # random — any reel
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page',1))
    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))
    return render(request, 'reels.html', {
        'page_obj': page_obj,
        'liked_ids': liked_ids,
    })

def feed_view(request):
    if request.user.is_authenticated:
        following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
        allowed_ids = following_ids + [request.user.id]
        qs = Post.objects.filter(author_id__in=allowed_ids, is_deleted=False)\
            .select_related('author')\
            .prefetch_related('images', 'likes')\
            .order_by('-created_at')
    else:
        qs = Post.objects.filter(is_deleted=False)\
            .select_related('author')\
            .prefetch_related('images', 'likes')\
            .order_by('-created_at')

    paginator = Paginator(qs, 20)
    page_num = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_num)
    except EmptyPage:
        page_obj = paginator.get_page(1)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        posts_data = []
        for post in page_obj:
            posts_data.append({
                'id': post.id,
                'author': post.author.username,
                'content': post.content,
                'created_at': post.created_at.isoformat(),
                'images': [img.image.url for img in post.images.all()],
                'likes_count': post.likes.count(),
                'is_liked': post.likes.filter(user=request.user).exists() if request.user.is_authenticated else False,
            })
        return JsonResponse({
            'posts': posts_data,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    # For like button state in feed
    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))

    # Stories — saare dikho kaun story dala (ring wale), nahi dane grey
    stories = []
    story_mentions = set()
    if request.user.is_authenticated:
        from accounts.models import Profile, Story
        from django.utils import timezone
        now = timezone.now()
        active_qs = Story.objects.filter(expires_at__gt=now)
        active_set = set(active_qs.values_list('user_id', flat=True))
        active_map = {st.user_id: st for st in active_qs.order_by('-created_at') if st.user_id not in {}}  # dedup latest handled below
        # rebuild map latest per user
        active_map = {}
        for st in active_qs.order_by('-created_at'):
            if st.user_id not in active_map:
                active_map[st.user_id] = st
        # Your story
        try:
            me_profile = request.user.profile
            me_profile.has_story = request.user.id in active_set
            me_profile.story_id = active_map[request.user.id].id if request.user.id in active_map else None
            stories.append(me_profile)
        except Profile.DoesNotExist:
            pass
        # Followed + top users sab dikhao, ring se pata chalega kaun dala
        candidates = []
        if following_ids:
            candidates = list(Profile.objects.filter(user_id__in=following_ids).select_related('user')[:12])
        if len(candidates) < 8:
            extra = Profile.objects.exclude(user_id__in=following_ids + [request.user.id]).order_by('-followers_count')[:8]
            seen = {p.user_id for p in candidates} | {request.user.id}
            for p in extra:
                if p.user_id not in seen:
                    candidates.append(p)
                    if len(candidates) >= 8:
                        break
        for p in candidates:
            p.has_story = p.user_id in active_set
            if p.has_story:
                p.story_id = active_map[p.user_id].id
            else:
                p.story_id = None
            stories.append(p)
        # Mention badge
        if following_ids:
            recent_mentions = Post.objects.filter(author_id__in=following_ids, is_deleted=False).order_by('-created_at')[:20]
            me = request.user.username.lower()
            for p in recent_mentions:
                if me in (p.tagged or '').lower() or f"@{me}" in p.content.lower():
                    story_mentions.add(p.author_id)
    # Right rail suggested
    suggested = []
    trending = []
    if request.user.is_authenticated:
        from accounts.models import Profile
        suggested = Profile.objects.exclude(user_id__in=following_ids + [request.user.id]).order_by('-followers_count')[:4]

    return render(request, 'posts/feed.html', {
        'page_obj': page_obj,
        'is_authenticated': request.user.is_authenticated,
        'liked_ids': liked_ids,
        'stories': stories,
        'story_mentions': story_mentions,
        'suggested': suggested,
        'trending': trending,
    })


@login_required
def post_create_view(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST)
        # Functional: location + tagged
        location = request.POST.get('location','').strip()[:100]
        tagged = request.POST.get('tagged','').strip()[:200]
        images = request.FILES.getlist('images')
        img_error = None
        if len(images) > 4:
            img_error = "Max 4 images allowed!"
        else:
            for img in images:
                if img.size > 5 * 1024 * 1024:
                    img_error = f"{img.name} > 5MB!"
                    break
                if not img.content_type.startswith('image/'):
                    img_error = f"{img.name} is not an image!"
                    break
        if img_error:
            messages.error(request, img_error)
        elif form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.location = location
            post.tagged = tagged
            post.save()
            for idx, img in enumerate(images[:4]):
                PostImage.objects.create(post=post, image=img, order=idx)
            messages.success(request, "Post created! 🎉")
            return redirect('posts:detail', pk=post.pk)
        elif not img_error:
            messages.error(request, "Fix errors.")
    else:
        form = PostCreateForm()
    return render(request, 'posts/create.html', {'form': form})


def post_detail_view(request, pk):
    post = get_object_or_404(Post.objects.select_related('author').prefetch_related('images', 'likes', 'comments__user', 'comments__replies'), pk=pk)
    if post.is_deleted and not (request.user.is_authenticated and request.user == post.author):
        from django.http import Http404
        raise Http404("Post deleted")
    top_comments = post.comments.filter(parent_comment__isnull=True).select_related('user').prefetch_related('replies__user').order_by('created_at')
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(user=request.user).exists()
    # Comment form for detail page
    comment_form = CommentForm()
    return render(request, 'posts/detail.html', {
        'post': post,
        'top_comments': top_comments,
        'is_liked': is_liked,
        'is_author': request.user == post.author if request.user.is_authenticated else False,
        'comment_form': comment_form,
    })


@login_required
def post_delete_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("Only author can delete!")
    if request.method == 'POST':
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])
        messages.info(request, "Post deleted (soft delete).")
        return redirect('posts:feed')
    return render(request, 'posts/delete_confirm.html', {'post': post})


# ============ SOCIAL: Like/Comment ============

@login_required
def like_toggle_view(request, pk):
    """
    POST /posts/<pk>/like/ -> toggle like, AJAX JSON
    Hinglish: Dubara press karo to unlike
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
        # Notification: post/reel like
        if post.author != request.user:
            from accounts.models import Notification
            ntype = 'reel_like' if 'reels' in request.META.get('HTTP_REFERER','') else 'like'
            Notification.objects.create(recipient=post.author, actor=request.user, type=ntype, post=post)
    likes_count = post.likes.count()
    # AJAX ya normal? Dono handle
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_liked': is_liked, 'likes_count': likes_count})
    # Non-AJAX fallback
    messages.info(request, "Liked!" if is_liked else "Unliked")
    return redirect('posts:detail', pk=pk)


@login_required
def comment_create_view(request, pk):
    """
    POST /posts/<pk>/comment/ -> comment ya reply
    Form fields: content, parent (optional hidden)
    """
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    if request.method != 'POST':
        return redirect('posts:detail', pk=pk)
    form = CommentForm(request.POST)
    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)
        # 1-level check: parent ka parent nahi hona chahiye
        if parent.parent_comment is not None:
            messages.error(request, "Only 1-level replies allowed!")
            return redirect('posts:detail', pk=pk)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        comment.parent_comment = parent
        comment.save()
        if post.author != request.user:
            from accounts.models import Notification
            Notification.objects.create(recipient=post.author, actor=request.user, type='comment', post=post)
        messages.success(request, "Comment added!")
    else:
        messages.error(request, "Comment max 200 chars, empty nahi!")
    return redirect('posts:detail', pk=pk)


def _is_within_5min(comment):
    return timezone.now() - comment.created_at <= timedelta(minutes=5)


@login_required
def comment_edit_view(request, pk):
    """
    POST /comments/<pk>/edit/ -> edit within 5 min, sirf author
    """
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    if not _is_within_5min(comment):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': '5 min limit over'}, status=403)
        messages.error(request, "Edit only within 5 minutes!")
        return redirect('posts:detail', pk=comment.post.pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content or len(content) > 200:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid content (max 200)'}, status=400)
            messages.error(request, "Invalid content (max 200, not empty)!")
            return redirect('posts:detail', pk=comment.post.pk)
        comment.content = content
        comment.save(update_fields=['content', 'updated_at'])
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'content': comment.content, 'id': comment.pk})
        messages.success(request, "Comment updated!")
        return redirect('posts:detail', pk=comment.post.pk)
    return render(request, 'posts/comment_edit.html', {'comment': comment})


@login_required
def comment_delete_view(request, pk):
    """
    POST /comments/<pk>/delete/ -> delete within 5 min, sirf author
    """
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    if not _is_within_5min(comment):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': '5 min limit over'}, status=403)
        messages.error(request, "Delete only within 5 minutes!")
        return redirect('posts:detail', pk=comment.post.pk)
    if request.method == 'POST':
        post_pk = comment.post.pk
        comment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'deleted': True})
        messages.info(request, "Comment deleted!")
        return redirect('posts:detail', pk=post_pk)
    return render(request, 'posts/comment_confirm_delete.html', {'comment': comment})
