from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Favorite
from listings.models import Listing

@login_required
def favorites_list_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('listing', 'listing__category', 'listing__owner').prefetch_related('listing__images')
    
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_favorites': favorites.count()
    }
    return render(request, 'favorites/list.html', context)

@login_required
@require_POST
def toggle_favorite_view(request):
    listing_id = request.POST.get('listing_id')
    
    if not listing_id:
        return JsonResponse({'error': 'Listing ID is required'}, status=400)
    
    try:
        listing = get_object_or_404(Listing, id=listing_id, status='active')
        
        # check if user wants to add to favorites his own listings
        if listing.owner == request.user:
            return JsonResponse({'error': 'Nu poți adăuga propriile anunțuri la favorite'}, status=400)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if not created:
            favorite.delete()
            is_favorited = False
            message = 'Anunțul a fost eliminat din favorite'
        else:
            # if favorite doesn t exist, create it
            is_favorited = True
            message = 'Anunțul a fost adăugat la favorite'
        
        response_data = {
            'success': True,
            'is_favorited': is_favorited,
            'message': message,
            'favorites_count': Favorite.objects.filter(user=request.user).count()
        }
        
        return JsonResponse(response_data)
        
    except Listing.DoesNotExist:
        return JsonResponse({'error': 'Anunțul nu a fost găsit'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'A apărut o eroare'}, status=500)

@login_required
def remove_favorite_view(request, favorite_id):
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    listing_title = favorite.listing.title
    favorite.delete()
    
    messages.success(request, f'Anunțul "{listing_title}" a fost eliminat din favorite.')
    return redirect('favorites:list')
