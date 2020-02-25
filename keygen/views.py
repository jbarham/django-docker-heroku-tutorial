import time

from django.shortcuts import render, redirect
from django.contrib import messages

from django_rq import job

from .models import Secret

# https://github.com/rq/django-rq#job-decorator
@job
def generate_bg():
    time.sleep(2) # Simulate expensive operation.
    Secret.objects.create()

def index(request):
    context = {'secrets': Secret.objects.all()}
    return render(request, 'keygen/index.html', context)

def generate(request):
    if request.GET.get('bg'):
        generate_bg.delay()
        messages.success(request, 'Generating new key in background. Refresh page after two seconds to see generated key.')
    else:
        Secret.objects.create()
        messages.success(request, 'Generated new key.')
    return redirect('home')

def delete(request):
    Secret.objects.all().delete()
    messages.success(request, 'Deleted all keys.')
    return redirect('home')
