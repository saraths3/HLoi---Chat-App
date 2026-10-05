from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home_page'),
    path('profile/', views.profile_view, name='profile_page'),
    path('search/', views.search_view, name='search_page'),
    path('search/send/<uuid:pid>/', views.send_fr_view, name='send_fr'),
    path('accept-request/<int:request_id>/', views.accept_fr, name='accept_fr'),
    path('reject-request/<int:request_id>/', views.reject_fr, name='reject_fr'),
    path('friends/', views.friends_view, name='friends_page'),
    path('alerts/', views.alerts_view, name='alerts_page'),
]