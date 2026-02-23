from django.contrib import admin
from .models import User, Event, Registration

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'time', 'status', 'capacity')
    list_filter = ('status', 'category', 'date')
    search_fields = ('title', 'organizer', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at')
    list_filter = ('registered_at', 'event')
    search_fields = ('user__name', 'event__title')
    readonly_fields = ('registered_at',)
