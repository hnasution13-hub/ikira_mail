from django.urls import path
from . import views

app_name = 'mail'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('compose/', views.compose, name='compose'),
    path('email/<int:email_id>/', views.view_email, name='view_email'),
    path('email/<int:email_id>/delete/', views.delete_email, name='delete_email'),
    path('email/<int:email_id>/star/', views.toggle_star, name='toggle_star'),
    path('contacts/', views.contacts, name='contacts'),
    path('contacts/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
]