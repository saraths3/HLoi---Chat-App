from django.shortcuts import render, redirect
from django.contrib.auth import logout


def sign_in_view(request):
    if request.user.is_authenticated:
        return redirect('home_page')
    return render(request, 'accounts/socialaccounts/sign_in.html')


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('sign_in_page')