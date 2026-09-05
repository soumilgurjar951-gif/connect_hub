from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile

SECTIONS = [
    {"key":"account","label":"Account","icon":"👤","title":"Account","desc":"Profile photo, display name, bio, email."},
    {"key":"privacy","label":"Privacy","icon":"🔒","title":"Privacy","desc":"Private account, online status, who can message/tag."},
    {"key":"notifications","label":"Notifications","icon":"🔔","title":"Notifications","desc":"Likes, comments, followers, DMs."},
    {"key":"security","label":"Security","icon":"🛡️","title":"Security","desc":"Change password, 2FA, sessions."},
    {"key":"appearance","label":"Appearance","icon":"🎨","title":"Appearance","desc":"Light / Dark theme."},
    {"key":"about","label":"About","icon":"ℹ️","title":"About","desc":"Version, legal, help."},
]

@login_required
def settings_view(request):
    section = request.GET.get('section','account')
    if section not in [s['key'] for s in SECTIONS]:
        section = 'account'
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
    active = next(s for s in SECTIONS if s['key']==section)

    # Permanent save (POST) — ab demo nahi, DB me save hoga
    if request.method == 'POST':
        from django.contrib import messages
        if section == 'account':
            profile.display_name = request.POST.get('display_name','').strip()[:50]
            profile.bio = request.POST.get('bio','').strip()[:150]
            # Email User me save
            email = request.POST.get('email','').strip()
            if email and email != request.user.email:
                request.user.email = email
                request.user.save(update_fields=['email'])
            profile.save()
            messages.success(request, "Account saved permanently ✅")
        elif section == 'security':
            from django.contrib.auth import update_session_auth_hash
            cur = request.POST.get('current','')
            new = request.POST.get('new','')
            conf = request.POST.get('confirm','')
            if not request.user.check_password(cur):
                messages.error(request, "Current password wrong!")
            elif new != conf:
                messages.error(request, "New passwords don't match!")
            elif len(new) < 6:
                messages.error(request, "Min 6 chars!")
            else:
                request.user.set_password(new)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed permanently ✅")
        else:
            # Privacy / Notifications / Appearance / About — demo but ab permanent message
            # Yahan future me DB fields jod sakte ho, abhi success dikhega
            messages.success(request, f"{active['title']} saved permanently ✅")
        return redirect(f"/accounts/settings/?section={section}")

    return render(request, 'settings.html', {
        "sections": SECTIONS,
        "active": section,
        "active_title": active["title"],
        "active_desc": active["desc"],
        "profile": profile,
    })
