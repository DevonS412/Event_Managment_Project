from django.urls import path
from . import views

urlpatterns = [
    # Original template views
    path('events/', views.events, name='events'),
    path('details/', views.details, name='details'),
    
    # User Authentication
    path('api/register/', views.register_user, name='register_user'),
    path('api/login/', views.login_user, name='login_user'),
    path('api/logout/', views.logout_user, name='logout_user'),
    
    # Event Viewing
    path('api/events/all/', views.get_all_events, name='get_all_events'),
    path('api/events/<int:event_id>/', views.get_event_details, name='get_event_details'),
    path('api/events/search/', views.search_events, name='search_events'),
    
    # Event Creation & Management
    path('api/events/create/', views.create_event, name='create_event'),
    path('api/events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('api/events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # Admin Event Approval
    path('api/admin/events/pending/', views.get_pending_events, name='get_pending_events'),
    path('api/admin/events/<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('api/admin/events/<int:event_id>/reject/', views.reject_event, name='reject_event'),
    
    # Event Registration
    path('api/events/<int:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('api/events/<int:event_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('api/user/events/', views.get_user_events, name='get_user_events'),
    path('api/events/<int:event_id>/attendees/', views.get_event_attendees, name='get_event_attendees'),
]