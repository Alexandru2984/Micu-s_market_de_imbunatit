from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import UserProfile
from listings.models import Listing

def register_view(request):
    if request.user.is_authenticated:
        return redirect('listings:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul pentru {username} a fost creat cu succes! Te poți autentifica acum.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('listings:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'listings:home')
                messages.success(request, f'Bine ai venit, {user.get_full_name() or user.username}!')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'account/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Te-ai deconectat cu succes!')
    return redirect('listings:home')

@login_required
def profile_view(request):
    # check if user has a profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # calculate stats
    user_stats = {
        'total_listings': Listing.objects.filter(owner=request.user).count(),
        'active_listings': Listing.objects.filter(owner=request.user, status='active').count(),
        'sold_listings': Listing.objects.filter(owner=request.user, status='sold').count(),
        'member_since': request.user.date_joined,
    }
    
    context = {
        'profile': profile,
        'user_stats': user_stats,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilul a fost actualizat cu succes!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/profile_edit.html', context)

def public_profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # active listings of user
    listings = Listing.objects.filter(owner=user, status='active').order_by('-created_at')[:6]
    
    # public stats
    user_stats = {
        'total_listings': Listing.objects.filter(owner=user, status='active').count(),
        'member_since': user.date_joined,
        'average_rating': profile.average_rating,
    }
    
    context = {
        'profile_user': user,
        'profile': profile,
        'listings': listings,
        'user_stats': user_stats,
    }
    return render(request, 'accounts/public_profile.html', context)

@login_required
def my_listings_view(request):
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    
    # filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        listings = listings.filter(status=status_filter)
    
    paginator = Paginator(listings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'listings/my_listings.html', context)
