from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('register/', views.register_view, name='register'),

    path('add-client/', views.add_client, name='add_client'),
    path('add-account/', views.add_account, name='add_account'),
    path('transfer/', views.transfer_money, name='transfer_money'),

    path('account/<int:id>/', views.account_detail, name='account_detail'),
    path('account/<int:id>/edit/', views.edit_account, name='edit_account'),
    path('account/<int:id>/delete/', views.delete_account, name='delete_account'),
    path('account/<int:id>/pdf/', views.export_pdf, name='export_pdf'),
]
