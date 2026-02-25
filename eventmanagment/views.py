from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
import json
from .models import User, Event, Registration


# ===== USER AUTHENTICATION =====

@require_http_methods(["POST"])
def register_user(request):
    """Create a new user account"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'student')
        
        if not name or not email or not password:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        user = User.objects.create(name=name, email=email, password=password, role=role)
        return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def login_user(request):
    """Log in a user"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)
        
        user = User.objects.filter(email=email, password=password).first()
        
        if not user:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        request.session['user_id'] = user.id
        return JsonResponse({'message': 'Login successful', 'user_id': user.id, 'role': user.role}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def logout_user(request):
    """Log out a user"""
    if 'user_id' in request.session:
        del request.session['user_id']
    return JsonResponse({'message': 'Logout successful'}, status=200)


# ===== EVENT VIEWING =====

def get_all_events(request):
    """Get all approved events"""
    events = Event.objects.filter(status='approved').values(
        'id', 'title', 'description', 'date', 'time', 'location', 
        'category', 'organizer', 'capacity', 'status'
    ).order_by('-date')
    
    return JsonResponse({'events': list(events)}, safe=False)


def get_event_details(request, event_id):
    """Get details for a specific event"""
    try:
        event = Event.objects.get(id=event_id, status='approved')
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date,
            'time': event.time,
            'location': event.location,
            'category': event.category,
            'organizer': event.organizer,
            'capacity': event.capacity,
            'registered_count': event.registration_set.count(),
        }
        
        return JsonResponse(event_data, status=200)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)


def search_events(request):
    """Search events by title, location, or category"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    events = Event.objects.filter(status='approved')
    
    if query:
        events = events.filter(title__icontains=query) | events.filter(location__icontains=query)
    
    if category:
        events = events.filter(category=category)
    
    event_list = events.values(
        'id', 'title', 'description', 'date', 'time', 'location', 'category', 'organizer'
    ).order_by('-date')
    
    return JsonResponse({'events': list(event_list)}, safe=False)


# ===== EVENT CREATION & MANAGEMENT =====

@require_http_methods(["POST"])
def create_event(request):
    """Create a new event (admin/staff only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role not in ['staff', 'admin']:
            return JsonResponse({'error': 'Only staff and admins can create events'}, status=403)
        
        data = json.loads(request.body)
        
        required_fields = ['title', 'description', 'date', 'time', 'location', 'category', 'capacity']
        if not all(field in data for field in required_fields):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        event = Event.objects.create(
            title=data['title'],
            description=data['description'],
            date=data['date'],
            time=data['time'],
            location=data['location'],
            category=data['category'],
            organizer=data.get('organizer', user.name),
            capacity=data['capacity'],
            status='pending'  # Events need admin approval
        )
        
        return JsonResponse({'message': 'Event created successfully', 'event_id': event.id}, status=201)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def edit_event(request, event_id):
    """Edit an event (admin/staff only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role not in ['staff', 'admin']:
            return JsonResponse({'error': 'Only staff and admins can edit events'}, status=403)
        
        event = Event.objects.get(id=event_id)
        data = json.loads(request.body)
        
        # Update only provided fields
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'date' in data:
            event.date = data['date']
        if 'time' in data:
            event.time = data['time']
        if 'location' in data:
            event.location = data['location']
        if 'category' in data:
            event.category = data['category']
        if 'capacity' in data:
            event.capacity = data['capacity']
        
        event.save()
        return JsonResponse({'message': 'Event updated successfully'}, status=200)
    
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def delete_event(request, event_id):
    """Delete an event (admin only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Only admins can delete events'}, status=403)
        
        event = Event.objects.get(id=event_id)
        event.delete()
        return JsonResponse({'message': 'Event deleted successfully'}, status=200)
    
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== ADMIN EVENT APPROVAL =====

@require_http_methods(["POST"])
def approve_event(request, event_id):
    """Approve a pending event (admin only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Only admins can approve events'}, status=403)
        
        event = Event.objects.get(id=event_id, status='pending')
        event.status = 'approved'
        event.save()
        return JsonResponse({'message': 'Event approved'}, status=200)
    
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found or already processed'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def reject_event(request, event_id):
    """Reject a pending event (admin only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Only admins can reject events'}, status=403)
        
        event = Event.objects.get(id=event_id, status='pending')
        event.status = 'rejected'
        event.save()
        return JsonResponse({'message': 'Event rejected'}, status=200)
    
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found or already processed'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_pending_events(request):
    """Get all pending events (admin only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        if user.role != 'admin':
            return JsonResponse({'error': 'Only admins can view pending events'}, status=403)
        
        events = Event.objects.filter(status='pending').values(
            'id', 'title', 'description', 'date', 'time', 'location', 'organizer'
        )
        return JsonResponse({'events': list(events)}, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== EVENT REGISTRATION =====

@require_http_methods(["POST"])
def register_for_event(request, event_id):
    """Register a user for an event"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        event = Event.objects.get(id=event_id, status='approved')
        
        # Check if already registered
        if Registration.objects.filter(user=user, event=event).exists():
            return JsonResponse({'error': 'Already registered for this event'}, status=400)
        
        # Check if event is full
        if event.registration_set.count() >= event.capacity:
            return JsonResponse({'error': 'Event is full'}, status=400)
        
        Registration.objects.create(user=user, event=event)
        return JsonResponse({'message': 'Registered successfully'}, status=201)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def cancel_registration(request, event_id):
    """Cancel registration for an event"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        registration = Registration.objects.get(user=user, event_id=event_id)
        registration.delete()
        return JsonResponse({'message': 'Registration cancelled'}, status=200)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Registration not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_user_events(request):
    """Get all events a user is registered for"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        registrations = Registration.objects.filter(user=user).select_related('event')
        
        events = [{
            'id': reg.event.id,
            'title': reg.event.title,
            'date': reg.event.date,
            'time': reg.event.time,
            'location': reg.event.location,
            'registered_at': reg.registered_at
        } for reg in registrations]
        
        return JsonResponse({'events': events}, safe=False)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_event_attendees(request, event_id):
    """Get list of attendees for an event (admin/organizer only)"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        user = User.objects.get(id=user_id)
        event = Event.objects.get(id=event_id)
        
        if user.role != 'admin':
            return JsonResponse({'error': 'Only admins can view attendee lists'}, status=403)
        
        registrations = Registration.objects.filter(event=event).select_related('user')
        attendees = [{
            'name': reg.user.name,
            'email': reg.user.email,
            'registered_at': reg.registered_at
        } for reg in registrations]
        
        return JsonResponse({'attendees': attendees, 'total': len(attendees)}, safe=False)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== ORIGINAL TEMPLATE VIEWS =====

def events(request):
  template = loader.get_template('events.html')
  return HttpResponse(template.render())

def details(request):
  template = loader.get_template('details.html')
  return HttpResponse(template.render())