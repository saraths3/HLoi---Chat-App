from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Profile, Friendship
from .forms import ProfileForm
from .signals import get_user_profile


def _get_safe_redirect(request, default_url_name):
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(default_url_name)


@login_required(login_url='sign_in_page')
def home_view(request):
    user_profile = get_user_profile(request.user)
    query = request.GET.get('q', '').strip()
    friends = Friendship.objects.filter(Q(reciever_profile = user_profile)| Q(sender_profile = user_profile)).filter(status = 'accepted')
    if query.startswith('@'):
        friends = friends.filter(Q(reciever_profile__username__exact = query[1:])|
                                 Q(sender_profile__username__exact = query[1:]))
    elif query:
        friends = friends.filter(Q(reciever_profile__name__icontains = query)| 
                                 Q(sender_profile__name__icontains = query))
    return render(request, 'core/home_page.html', {'profile': user_profile, 'friends': friends, 'query': query})


@login_required(login_url='sign_in_page')
def profile_view(request):
    existing_profile = get_user_profile(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=existing_profile)
        if form.is_valid():
            updated_profile = form.save(commit=False)
            updated_profile.user = request.user
            updated_profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_page')
    else:
        form = ProfileForm(instance=existing_profile)
    return render(request, 'core/profile_page.html', {'form': form})


@login_required(login_url='sign_in_page')
def search_view(request):
    user_profile = get_user_profile(request.user)
    query = request.GET.get('q', '').strip()

    profiles = Profile.objects.exclude(id=user_profile.id)

    if query:
        if query.startswith('@'):
            profiles = profiles.filter(username__iexact=query[1:])
        else:
            profiles = profiles.filter(
                Q(name__icontains=query) | Q(username__icontains=query)
            )

    user_friendships = Friendship.objects.filter(
        Q(reciever_profile=user_profile) | Q(sender_profile=user_profile)
    )

    friendship_map = {}
    for f in user_friendships:
        if f.reciever_profile_id == user_profile.id:
            other_id = f.sender_profile_id
        else:
            other_id = f.reciever_profile_id
        
        friendship_map[other_id] = f

    for profile in profiles:
        friendship = friendship_map.get(profile.id)
        if friendship:
            profile.friendship_status = friendship.status
            profile.is_sender = (friendship.sender_profile_id == user_profile.id)
            profile.friendship_id = friendship.id
        else:
            profile.friendship_status = None
            profile.is_sender = False
            profile.friendship_id = None

    context = {
        'query': query,
        'profiles': profiles,
    }
    return render(request, 'core/search.html', context)


@login_required(login_url='sign_in_page')
@require_POST
def send_fr_view(request, pid):
    user_profile = get_user_profile(request.user)
    reciver_profile = get_object_or_404(Profile, id=pid)

    if user_profile.id == reciver_profile.id:
        messages.error(request, 'You cannot send a friend request to yourself.')
        return _get_safe_redirect(request, 'search_page')

    existing = Friendship.objects.filter(
        (Q(sender_profile=user_profile, reciever_profile=reciver_profile) |
         Q(sender_profile=reciver_profile, reciever_profile=user_profile))
    ).first()

    if existing:
        if existing.status == 'accepted':
            messages.info(request, f'You are already friends with {reciver_profile.username}.')
        elif existing.status == 'pending':
            if existing.sender_profile_id == user_profile.id:
                messages.info(request, f'Friend request to {reciver_profile.username} has already been sent.')
            else:
                messages.info(request, f'{reciver_profile.username} has already sent you a friend request.')
        elif existing.status == 'rejected':
            existing.sender_profile = user_profile
            existing.reciever_profile = reciver_profile
            existing.status = 'pending'
            existing.save()
            messages.success(request, f'Friend request sent to {reciver_profile.username}.')
    else:
        try:
            Friendship.objects.create(
                sender_profile=user_profile,
                reciever_profile=reciver_profile,
                status='pending'
            )
            messages.success(request, f'Friend request sent to {reciver_profile.username}.')
        except ValidationError as e:
            err_msg = e.message if hasattr(e, 'message') else (e.messages[0] if hasattr(e, 'messages') else str(e))
            messages.error(request, err_msg)
        except IntegrityError:
            messages.error(request, 'A friend request between these profiles already exists.')

    return _get_safe_redirect(request, 'search_page')


@login_required(login_url='sign_in_page')
@require_POST
def accept_fr(request, request_id):
    user_profile = get_user_profile(request.user)
    friend_request = get_object_or_404(Friendship, id=request_id, reciever_profile=user_profile)
    friend_request.status = 'accepted'
    friend_request.save()
    messages.success(request, f'Friend request from {friend_request.sender_profile.username} accepted.')
    return _get_safe_redirect(request, 'alerts_page')


@login_required(login_url='sign_in_page')
@require_POST
def reject_fr(request, request_id):
    user_profile = get_user_profile(request.user)
    friend_request = get_object_or_404(Friendship, id=request_id, reciever_profile=user_profile)
    sender_username = friend_request.sender_profile.username
    friend_request.delete()
    messages.info(request, f'Friend request from {sender_username} declined.')
    return _get_safe_redirect(request, 'alerts_page')


@login_required(login_url='sign_in_page')
def friends_view(request):
    user_profile = get_user_profile(request.user)
    query = request.GET.get('q', '').strip()
    friendships = Friendship.objects.filter(
        Q(sender_profile=user_profile) | Q(reciever_profile=user_profile),
        status='accepted'
    ).select_related('sender_profile', 'reciever_profile')
    
    for f in friendships:
        f.friend = f.sender_profile if f.reciever_profile_id == user_profile.id else f.reciever_profile
    if query:
        friendships = friendships.filter(sender_profile__name__icontains = query)
    context = {
        'profile': user_profile,
        'friendship': friendships,
        'friendships': friendships,
        'query': query,
    }
    return render(request, 'core/friends.html', context)


@login_required(login_url='sign_in_page')
def alerts_view(request):
    user_profile = get_user_profile(request.user)
    friend_requests = Friendship.objects.filter(
        reciever_profile=user_profile,
        status='pending'
    ).select_related('sender_profile')
    context = {
        'friend_requests': friend_requests
    }
    return render(request, 'core/alerts.html', context)

@login_required(login_url='sign_in_page')
def remove_friend(request, friend_id):
    if request.method == 'POST':
        friend_profile = get_object_or_404(Profile, id=friend_id)
        user_profile = request.user.profile
        friendship = Friendship.objects.filter(
            Q(sender_profile=friend_profile, reciever_profile=user_profile) |
            Q(sender_profile=user_profile, reciever_profile=friend_profile)
        ).first()
        if friendship:
            friendship.delete()

    return redirect('friends_page')