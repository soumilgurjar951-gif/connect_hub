"""
chat/views.py - 1-to-1 DM with polling
Hinglish: WhatsApp jaisa par simple, har 2 sec me naya message check (polling).
WebSocket baad me lagayenge, MVP me polling kaafi.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Max
from .models import Message, CallSignal
from .forms import MessageForm
import json


@login_required
def conversation_list_view(request):
    """
    Jinse chat kiya hai unki list + last message + unread count
    """
    user = request.user
    # Saare messages jisme user sender ya receiver hai
    msgs = Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender','receiver').order_by('-created_at')
    # Unique user ids nikalo
    seen = {}
    conversations = []
    for m in msgs:
        other = m.receiver if m.sender == user else m.sender
        if other.id not in seen:
            seen[other.id] = True
            # last message is m (kyunki -created_at order)
            unread = Message.objects.filter(sender=other, receiver=user, is_read=False).count()
            # Try to get profile username
            try:
                username = other.profile.username
            except:
                username = other.username
            conversations.append({
                'user': other,
                'username': username,
                'last_message': m,
                'unread': unread,
            })
        if len(conversations) >= 50:
            break

    # Filter: all / unread / groups
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        conversations = [c for c in conversations if c['unread'] > 0]
    elif filter_type == 'groups':
        # Groups — v2 feature, abhi empty
        conversations = []

    # Search? ?q=username
    q = request.GET.get('q', '').strip()
    if q:
        # Filter conversations where username contains q
        conversations = [c for c in conversations if q.lower() in c['username'].lower() or q.lower() in c['user'].username.lower()]
        # Also suggest users not yet chatted
        if len(conversations) == 0:
            from accounts.models import Profile
            suggestions = Profile.objects.filter(username__icontains=q).exclude(user=user)[:5]
        else:
            suggestions = []
    else:
        suggestions = []

    return render(request, 'chat/conversation_list.html', {
        'conversations': conversations,
        'q': q,
        'suggestions': suggestions,
        'filter': filter_type,
    })


@login_required
def chat_detail_view(request, username):
    """
    username wale user se chat
    - GET: messages dikhao + is_read True karo
    - POST: naya message bhejo
    - AJAX ?after=<id>: polling ke liye naye messages
    """
    # username -> User (Profile ya User se)
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(username__iexact=username)
        other = profile.user
    except:
        other = get_object_or_404(User, username__iexact=username)

    if other == request.user:
        from django.contrib import messages as dj_messages
        dj_messages.error(request, "You cannot chat with yourself!")
        return redirect('chat:conversation_list')

    # Polling: ?after=<id> -> return JSON new messages + call signals
    after = request.GET.get('after')
    if after and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            after_id = int(after)
            new_msgs = Message.get_conversation(request.user, other).filter(id__gt=after_id).order_by('created_at')[:50]
            call_after = request.GET.get('call_after', '0')
            try:
                ca = int(call_after)
            except:
                ca = 0
            signals = CallSignal.objects.filter(receiver=request.user, caller=other, is_read=False, id__gt=ca).order_by('created_at')[:10]
            return JsonResponse({
                'messages': [
                    {
                        'id': m.id,
                        'sender': m.sender.username,
                        'content': m.content,
                        'image': m.image.url if m.image else None,
                        'is_me': m.sender == request.user,
                        'created_at': m.created_at.strftime('%H:%M'),
                    } for m in new_msgs
                ],
                'calls': [
                    {'id': s.id, 'type': s.type, 'data': s.data, 'is_video': s.is_video, 'caller': s.caller.username}
                    for s in signals
                ]
            })
        except Exception as e:
            pass

    # Normal GET: mark received as read
    Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

    qs = Message.get_conversation(request.user, other).select_related('sender','receiver')
    # Handle POST send (text + photo)
    if request.method == 'POST':
        # Support both form and multipart (image)
        content = (request.POST.get('content') or '').strip()
        image = request.FILES.get('image')
        # Allow image-only (content can be blank if image present)
        if not content and not image:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Empty'}, status=400)
            messages_error = "Message cannot be empty!"
            return redirect('chat:chat_detail', username=username)
        # Validate via form if content present
        if content:
            form = MessageForm({'content': content})
            if not form.is_valid():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Invalid'}, status=400)
                return redirect('chat:chat_detail', username=username)
        if image and image.size > 5*1024*1024:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '>5MB'}, status=400)
            return redirect('chat:chat_detail', username=username)
        Message.objects.create(sender=request.user, receiver=other, content=content, image=image)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect('chat:chat_detail', username=username)
    else:
        form = MessageForm()

    # For JS: last message id
    last_id = qs.last().id if qs.exists() else 0

    try:
        other_username = other.profile.username
    except:
        other_username = other.username

    # Call signals: last id for polling
    last_call_id = CallSignal.objects.filter(receiver=request.user, caller=other).order_by('-id').first()
    last_call_id = last_call_id.id if last_call_id else 0

    return render(request, 'chat/detail.html', {
        'other': other,
        'other_username': other_username,
        'messages': qs,
        'form': form,
        'last_id': last_id,
        'last_call_id': last_call_id,
    })


@login_required
def call_signal_view(request, username):
    """POST offer/answer/ice/hangup -> polling"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(username__iexact=username)
        other = profile.user
    except:
        other = get_object_or_404(User, username__iexact=username)
    if other == request.user:
        return JsonResponse({'error': 'self not allowed'}, status=400)
    try:
        body = json.loads(request.body.decode() or '{}')
    except:
        body = request.POST.dict()
    sig_type = body.get('type') or body.get('signal_type')
    data = body.get('data') or body.get('sdp') or ''
    is_video = str(body.get('is_video', 'false')).lower() in ('1','true','yes')
    if sig_type not in ('offer','answer','ice','hangup'):
        return JsonResponse({'error': 'bad type'}, status=400)
    if isinstance(data, dict):
        data = json.dumps(data)
    # hangup: mark all as read + create hangup signal
    CallSignal.objects.create(caller=request.user, receiver=other, type=sig_type, data=data or '', is_video=is_video)
    # If hangup, mark previous as read
    if sig_type == 'hangup':
        CallSignal.objects.filter(caller=other, receiver=request.user).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required
def call_ack_view(request, username):
    """Mark signals as read after client processed"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(username__iexact=username)
        other = profile.user
    except:
        other = get_object_or_404(User, username__iexact=username)
    ids = request.POST.getlist('ids') or json.loads(request.body.decode() or '{}').get('ids', [])
    if ids:
        CallSignal.objects.filter(id__in=ids, receiver=request.user, caller=other).update(is_read=True)
    else:
        CallSignal.objects.filter(receiver=request.user, caller=other, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})
