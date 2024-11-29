from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='modify_objects/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='modify_objects/logout.html'), name='logout'),
    path('process_image/<int:image_id>/', views.process_image, name='process_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('add_image_feed/', views.add_image_feed, name='add_image_feed'),
    path('view_processed_image/<int:image_id>/', views.view_processed_image, name='view_processed_image'),
]
