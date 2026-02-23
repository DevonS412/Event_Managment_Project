from django.http import HttpResponse
from django.template import loader
from .models import Event

def events(request):
  events = Event.objects.all().values()
  template = loader.get_template('events.html')
  context = {
    'events': events,
  }
  return HttpResponse(template.render(context, request))


def details(request, id):
  event = Event.objects.get(id=id)
  template = loader.get_template('details.html')
  context = {
    'event': event,
  }
  return HttpResponse(template.render(context, request))