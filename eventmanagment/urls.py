from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.events, name='events'),
    path('events/details/<int:id>', views.details, name='details'),
]