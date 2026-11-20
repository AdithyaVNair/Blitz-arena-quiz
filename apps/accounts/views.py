from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
import urllib.parse
import json
import urllib.request
import secrets
from .forms import SignUpForm, AVATAR_CHOICES
from .models import User


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Blitz Arena, {user.username}!')
            return redirect('profile')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {
        'form': form,
        'google_configured': bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or 'profile'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {
        'form': form,
        'google_configured': bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    })


def google_login_view(request):
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))

    if not client_id or not client_secret:
        # Development mode simulation if credentials not set yet
        demo_username = f"google_player_{secrets.token_hex(3)}"
        user, created = User.objects.get_or_create(
            username=demo_username,
            defaults={
                'email': f"{demo_username}@gmail.com",
                'avatar': 'bot',
                'xp': 150
            }
        )
        login(request, user)
        messages.success(request, f"Signed in with Google (Dev Demo Account: {user.username})! Set GOOGLE_CLIENT_ID in .env for production credentials.")
        return redirect('profile')

    # Real Google OAuth2 flow
    state = secrets.token_urlsafe(16)
    request.session['google_oauth_state'] = state
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(url)


def google_callback_view(request):
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error or not code:
        messages.error(request, 'Google sign-in was canceled or failed.')
        return redirect('login')

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    # Exchange code for tokens
    try:
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }).encode('utf-8')
        
        req = urllib.request.Request('https://oauth2.googleapis.com/token', data=token_data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as resp:
            token_json = json.loads(resp.read().decode('utf-8'))
            access_token = token_json.get('access_token')

        # Fetch profile
        info_req = urllib.request.Request('https://www.googleapis.com/oauth2/v3/userinfo')
        info_req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(info_req) as info_resp:
            user_info = json.loads(info_resp.read().decode('utf-8'))
            
        email = user_info.get('email')
        name = user_info.get('name') or email.split('@')[0]
        base_username = ''.join(c for c in name.lower().replace(' ', '_') if c.isalnum() or c == '_')[:20] or 'player'

        user = User.objects.filter(email=email).first()
        if not user:
            # Create new user
            username = base_username
            idx = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{idx}"
                idx += 1
            user = User.objects.create_user(
                username=username,
                email=email,
                avatar='fox',
                xp=50
            )
        
        login(request, user)
        messages.success(request, f'Welcome to Blitz Arena, {user.username}!')
        return redirect('profile')
    except Exception as e:
        messages.error(request, f'Failed to authenticate with Google: {str(e)}')
        return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        avatar = request.POST.get('avatar')
        if avatar and any(avatar == c[0] for c in AVATAR_CHOICES):
            request.user.avatar = avatar
            request.user.save(update_fields=['avatar'])
            messages.success(request, 'Avatar updated!')
            return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'avatar_choices': AVATAR_CHOICES,
    })

