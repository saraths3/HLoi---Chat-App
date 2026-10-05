from django.urls import path
from . import views

urlpatterns = [
    path('signin/', views.sign_in_view, name='sign_in_page'),
    path('signout/', views.logout_view, name='logout_page'),
]