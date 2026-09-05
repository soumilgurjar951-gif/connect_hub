from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from django.contrib.auth.models import User

TAGS = ["Tech 💻","Music 🎵","Sports ⚽","Art 🎨","Gaming 🎮","Food 🍜","Travel ✈️","Memes 😂","Fitness 💪","Movies 🎬"]

@login_required
def step1(request):
    q = request.GET.get('q','').strip()
    if q:
        # Search par sab milega — naya member bhi
        suggested = Profile.objects.filter(username__icontains=q).exclude(user=request.user).select_related('user')[:8]
    else:
        # Bina search ke koi auto-suggestion nahi — naya member yahan auto nahi ayega
        suggested = []
    following_ids = set(request.user.following.values_list('following_id', flat=True))
    return render(request, 'onboarding/step1.html', {
        "suggested": suggested,
        "q": q,
        "following_ids": following_ids,
        "following_count": len(following_ids),
    })

@login_required
def step2(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
    selected = [s.strip() for s in (profile.interests or '').split(',') if s.strip()]
    if request.method == 'POST':
        interests = request.POST.getlist('interests')
        # strip emoji for storage
        interests = [i.split(' ')[0] for i in interests]
        profile.interests = ','.join(interests[:10])
        profile.save(update_fields=['interests'])
        return redirect('accounts:onboarding_step3')
    # clean tags for display (without emoji split)
    return render(request, 'onboarding/step2.html', {"tags": TAGS, "selected": profile.interests})

@login_required
def step3(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
    if request.method == 'POST':
        profile.display_name = request.POST.get('display_name','').strip()[:50]
        profile.bio = request.POST.get('bio','').strip()[:150]
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        profile.onboarding_done = True
        profile.save()
        messages.success(request, "Welcome! Your feed is ready 🎉")
        return redirect('posts:feed')
    return render(request, 'onboarding/step3.html', {"profile": profile})
