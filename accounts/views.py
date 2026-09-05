"""
accounts/views.py - Signup, Login, Logout, Profile
Hinglish: View = har URL pe kya dikhana hai, form handle karna.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .forms import SignupForm, ProfileEditForm
from .models import Profile, Follow
from posts.models import Post


def signup_view(request):
    """Naya user banane ka page"""
    if request.user.is_authenticated:
        return redirect('posts:feed')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # signup ke baad auto login
            messages.success(request, f"Welcome @{user.username}! Account created 🎉")
            return redirect('accounts:onboarding_step1')
        else:
            messages.error(request, "Please fix errors below.")
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


class CustomLoginView(LoginView):
    """Django ka built-in login, bas template change kiya"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back {form.get_user().username}!")
        return super().form_valid(form)


def logout_view(request):
    """Logout - GET se bhi ho jayega (simple MVP)"""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Logged out successfully.")
    return redirect('accounts:login')


def profile_view(request, username):
    """
    Kisi bhi user ka profile dekhna: /accounts/profile/<username>/
    """
    profile = get_object_or_404(Profile, username__iexact=username)
    posts = Post.objects.filter(author=profile.user, is_deleted=False).order_by('-created_at')[:20]
    is_following = False
    is_own_profile = False
    if request.user.is_authenticated:
        is_own_profile = (request.user == profile.user)
        if not is_own_profile:
            is_following = Follow.objects.filter(follower=request.user, following=profile.user).exists()

    suggested = []
    if request.user.is_authenticated:
        following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
        suggested = Profile.objects.exclude(user=request.user).exclude(user_id__in=following_ids).order_by('-followers_count')[:6]
    else:
        suggested = Profile.objects.exclude(user=profile.user).order_by('-followers_count')[:6]

    # Tagged posts: jahan is profile ko tag kiya gaya (@username in tagged field ya content me)
    from django.db.models import Q
    tagged_posts = Post.objects.filter(
        Q(tagged__icontains=profile.username) | Q(content__icontains=f"@{profile.username}"),
        is_deleted=False
    ).exclude(author=profile.user).select_related('author').prefetch_related('images').order_by('-created_at')[:12]

    context = {
        'profile': profile,
        'posts': posts,
        'posts_count': posts.count(),
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'suggested': suggested,
        'tagged_posts': tagged_posts,
    }
    return render(request, 'accounts/profile.html', context)


def suggested_view(request):
    """See all -> suggestion panel (pura)"""
    from django.contrib.auth.decorators import login_required
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    suggestions = Profile.objects.exclude(user=request.user).exclude(user_id__in=following_ids).order_by('-followers_count')[:30]
    return render(request, 'accounts/suggested.html', {'suggestions': suggestions})

def followers_list_view(request, username):
    """Kaun kaun follow karta hai — 0 followers wale pe bhi page khulega"""
    profile = get_object_or_404(Profile, username__iexact=username)
    # Follow.following == profile.user  => follower list
    follows = Follow.objects.filter(following=profile.user).select_related('follower__profile').order_by('-created_at')
    # For button state: jinhe mai follow karta hu
    my_following = set()
    if request.user.is_authenticated:
        my_following = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    return render(request, 'accounts/follow_list.html', {
        'profile': profile,
        'type': 'followers',
        'title': 'Followers',
        'follows': follows,
        'my_following': my_following,
    })


def following_list_view(request, username):
    """Mai kinko follow karta hu"""
    profile = get_object_or_404(Profile, username__iexact=username)
    follows = Follow.objects.filter(follower=profile.user).select_related('following__profile').order_by('-created_at')
    my_following = set()
    if request.user.is_authenticated:
        my_following = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    return render(request, 'accounts/follow_list.html', {
        'profile': profile,
        'type': 'following',
        'title': 'Following',
        'follows': follows,
        'my_following': my_following,
    })


@login_required
def profile_edit_view(request):
    """Apna profile edit karna - sirf logged in user"""
    # Profile nahi hai to banao (admin user ke liye)
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'username': request.user.username, 'bio': ''}
    )
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Username change hua to User.username bhi update karo sync ke liye
            new_username = form.cleaned_data['username']
            if new_username != request.user.username:
                # Check User duplicate
                if User.objects.filter(username__iexact=new_username).exclude(pk=request.user.pk).exists():
                    form.add_error('username', 'Username taken in Users!')
                else:
                    request.user.username = new_username
                    request.user.save()
                    profile = form.save()
                    messages.success(request, "Profile updated!")
                    return redirect('accounts:profile', username=profile.username)
            else:
                form.save()
                messages.success(request, "Profile updated!")
                return redirect('accounts:profile', username=profile.username)
        else:
            messages.error(request, "Fix errors.")
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})


@login_required
def follow_toggle_view(request, username):
    """
    Follow/Unfollow toggle - POST se
    Hinglish: Button dabao to follow, dubara dabao to unfollow
    """
    target_profile = get_object_or_404(Profile, username__iexact=username)
    target_user = target_profile.user

    if target_user == request.user:
        messages.error(request, "You cannot follow yourself!")
        return redirect('accounts:profile', username=target_profile.username)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        # Already followed -> unfollow
        follow.delete()
        # Count update (denormalized)
        Profile.objects.filter(user=request.user).update(following_count=models.F('following_count') - 1)
        Profile.objects.filter(user=target_user).update(followers_count=models.F('followers_count') - 1)
        messages.info(request, f"Unfollowed @{target_profile.username}")
        is_following = False
    else:
        # New follow
        Profile.objects.filter(user=request.user).update(following_count=models.F('following_count') + 1)
        Profile.objects.filter(user=target_user).update(followers_count=models.F('followers_count') + 1)
        messages.success(request, f"Following @{target_profile.username}!")
        is_following = True
        from .models import Notification
        Notification.objects.create(recipient=target_user, actor=request.user, type='follow')

    # AJAX ke liye JSON bhi de sakte hain, MVP me redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        # Refresh counts
        target_profile.refresh_from_db()
        return JsonResponse({
            'is_following': is_following,
            'followers_count': target_profile.followers_count
        })

    return redirect('accounts:profile', username=target_profile.username)

# Import models for F() at bottom to avoid circular
from django.db import models
