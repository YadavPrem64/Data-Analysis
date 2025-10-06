from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('debug/', views.debug_auth_view, name='debug_auth'),
    path('users/', views.user_list_view, name='user_list'),
    path('database/', views.database_status_view, name='database_status'),
]