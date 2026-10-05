from django.shortcuts import redirect
from .models import Profile


def profile_required(get_response):
    def middleware(request):

        if request.user.is_authenticated:
            try:
                request.user.profile
            except Profile.DoesNotExist:

                if request.path != '/profile/':
                    return redirect('profile_page')

        return get_response(request)
    return middleware