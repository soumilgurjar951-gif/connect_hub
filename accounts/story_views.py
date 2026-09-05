from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Story, Profile

@login_required
def story_create_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        img = request.FILES['image']
        if img.size > 5*1024*1024:
            messages.error(request, ">5MB not allowed")
        elif not img.content_type.startswith('image/'):
            messages.error(request, "Only images")
        else:
            from datetime import timedelta
            Story.objects.create(user=request.user, image=img, expires_at=timezone.now()+timedelta(hours=24))
            messages.success(request, "Story shared! 24h tak dikhega ✨")
            return redirect('posts:feed')
    return render(request, 'accounts/story_create.html')

def story_view(request, pk):
    try:
        s = Story.objects.get(pk=pk)
    except Story.DoesNotExist:
        return render(request, 'accounts/story_expired.html', {"msg": "Story not found — maybe deleted."})
    if s.is_expired():
        return render(request, 'accounts/story_expired.html', {"msg": "Story expired — 24 hours ho gaye."})
    # Record view (agar viewer login hai aur owner nahi)
    viewers = []
    is_owner = False
    if request.user.is_authenticated:
        is_owner = (request.user == s.user)
        if not is_owner:
            from .models import StoryView
            StoryView.objects.get_or_create(story=s, viewer=request.user)
        # Owner ko dikhana kis kis ne dekha
        if is_owner:
            viewers = s.views.select_related('viewer__profile').order_by('-viewed_at')[:50]
    return render(request, 'accounts/story_detail.html', {'story': s, 'is_owner': is_owner, 'viewers': viewers})
