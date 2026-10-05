from django.shortcuts import render, redirect, get_object_or_404
from core.models import Profile, Friendship
from .models import Conversation, Message
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages

@login_required(login_url = 'sign_in_page')
def direct_chat_view(request, pid):
    user_profile = request.user.profile
    other_profile = get_object_or_404(Profile, id = pid)
    conversation = Conversation.objects.filter(type = 'direct', profiles = other_profile).filter(profiles = user_profile).first()
    if not conversation:
        conversation = Conversation.objects.create(type = 'direct')
        conversation.profiles.add(user_profile, other_profile)

    chat_messages =  conversation.messages.all().order_by('created_at')
    context = {
        'user_profile': user_profile,
        'other_profile': other_profile,
        'chat_messages': chat_messages,
    }
    return render(request, 'chat/direct_chat.html', context)

@login_required(login_url='sign_in_page')
def channels_view(request):
    user_profile = request.user.profile
    conversation = Conversation.objects.filter(type='channels', profiles__in=[user_profile]).exclude(admin=user_profile)
    my_conversations = Conversation.objects.filter(type='channels', profiles__in=[user_profile], admin=user_profile)
    if request.method == 'POST':
        status = request.POST.get('channel')
        if status == 'create':
            return redirect('channel_creation_page')
        return redirect('channels_page')
    return render(request, 'chat/channels.html', {'channels': conversation, 'my_channels': my_conversations})
    

@login_required(login_url='sign_in_page')
def channel_creation_view(request):
    user_profile = request.user.profile
    friendships = Friendship.objects.filter(Q(sender_profile = user_profile)| Q(reciever_profile = user_profile), status = 'accepted').select_related('sender_profile', 'reciever_profile')
    friends_profile = []
    for friend in friendships:
        if friend.sender_profile == user_profile:
            friends_profile.append(friend.reciever_profile)
        else:
            friends_profile.append(friend.sender_profile)
    if request.method == 'POST':
        channel_name = request.POST.get('name')
        selected_profile = request.POST.getlist('members')
        if selected_profile and channel_name:
            conversation = Conversation.objects.create(name = channel_name, type = 'channels', admin = user_profile)
            conversation.profiles.add(user_profile)
            for profile_id in selected_profile:
                profile = get_object_or_404(Profile, id = profile_id)
                conversation.profiles.add(profile)
                messages.success(request,f'Channel {conversation.name} Created' )
            return redirect('channels_page')
    context = {
        'friends': friends_profile,
    }
    return render(request, 'chat/channel_creation.html', context)

@login_required(login_url='accounts/socialaccounts/sign_in.html')
def channel_deletion_view(request, channel_id):
    channel = get_object_or_404(Conversation, type = 'channels', id = channel_id)
    user_profile = request.user.profile
    if request.method == 'POST':
        if channel.admin == user_profile:
            channel_name = channel.name
            channel.delete()
            messages.success(request, f'Channel { channel_name } Deleted Successfully.')
            return redirect('channels_page')
        else:
            messages.error(request, 'Permission Denied.')
            return redirect('channels_page')
    return render(request, 'chat/channel_deletion.html', {'channel':channel})

@login_required(login_url='sign_in_page')
def channel_chat_view(request, channel_id):
    channel = get_object_or_404(Conversation, id = channel_id)
    messages = Message.objects.filter(conversation = channel)
    context = {
        'channel_id':channel_id,
        'chat_messages': messages,
    }
    return render(request, 'chat/channel_chat.html', context)