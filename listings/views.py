from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Listing, ListingImage
from .forms import ListingForm, ListingImageFormSet
from categories.models import Category

def home_view(request):
    recent_listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images').order_by('-created_at')[:8]
    featured_listings = Listing.objects.filter(status='active', is_featured=True).select_related('category', 'owner').prefetch_related('images').order_by('-created_at')[:4]
    
    # favorites stat for authenticated user
    if request.user.is_authenticated:
        from favorites.models import Favorite
        user_favorites = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
        for listing in recent_listings:
            listing.is_favorited = listing.id in user_favorites
        for listing in featured_listings:
            listing.is_favorited = listing.id in user_favorites
    
    # numbers of listings for each category, includind subcategories
    categories = Category.objects.filter(is_active=True)
    categories_with_counts = []
    
    for category in categories:
        category_ids = [category.id] + [sub.id for sub in category.get_all_children]
        active_count = Listing.objects.filter(
            category_id__in=category_ids, 
            status='active'
        ).count()
        
        category.active_listings_count = active_count
        categories_with_counts.append(category)
    
    # first 12 categories after the number of listings
    categories_with_counts.sort(key=lambda x: x.active_listings_count, reverse=True)
    top_categories = categories_with_counts[:12]
    
    context = {
        'recent_listings': recent_listings,
        'featured_listings': featured_listings,
        'categories': top_categories,
    }
    return render(request, 'listings/home.html', context)

def listing_list_view(request):
    listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images')
    
    # sellers sorting
    seller = request.GET.get('seller')
    if seller:
        listings = listings.filter(owner__username=seller)
    
    # category sorting
    category_param = request.GET.get('category')
    selected_category = None
    if category_param:
        try:
            selected_category = Category.objects.get(slug=category_param, is_active=True)
            category_ids = [selected_category.id] + [sub.id for sub in selected_category.get_all_children]
            listings = listings.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            try:
                selected_category = Category.objects.get(id=category_param, is_active=True)
                category_ids = [selected_category.id] + [sub.id for sub in selected_category.get_all_children]
                listings = listings.filter(category_id__in=category_ids)
            except (Category.DoesNotExist, ValueError):
                pass
    
    # price sorting
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    
    # city sorting
    city = request.GET.get('city')
    if city:
        listings = listings.filter(city__icontains=city)
    
    # search
    search = request.GET.get('search')
    if search:
        listings = listings.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'title', '-title']
    if sort_by in valid_sorts:
        listings = listings.order_by(sort_by)
    else:
        listings = listings.order_by('-created_at')
    
    # pagination
    paginator = Paginator(listings, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.user.is_authenticated:
        from favorites.models import Favorite
        user_favorites = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
        for listing in page_obj:
            listing.is_favorited = listing.id in user_favorites
    
    # templates context
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': selected_category,
        'current_category_slug': category_param,
        'current_city': city,
        'current_seller': seller,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search,
        'sort_by': sort_by,
    }
    return render(request, 'listings/list.html', context)

def listing_detail_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # numbers of views for each listing
    listing.views_count += 1
    listing.save(update_fields=['views_count'])
    
    # check for favorite listing if user is authenticated
    is_favorited = False
    if request.user.is_authenticated:
        from favorites.models import Favorite
        is_favorited = Favorite.objects.filter(user=request.user, listing=listing).exists()
    
    # similar listings
    similar_listings = Listing.objects.filter(
        category=listing.category,
        status='active'
    ).exclude(id=listing.id).prefetch_related('images')[:4]
    
    context = {
        'listing': listing,
        'similar_listings': similar_listings,
        'is_favorited': is_favorited,
    }
    return render(request, 'listings/detail.html', context)

def process_images(request, listing):
    images = request.FILES.getlist('images')
    for image in images:
        if image:
            try:
                ListingImage.objects.create(
                    listing=listing,
                    image=image,
                    alt_text=f"Imagine pentru {listing.title}"
                )
            except Exception as e:
                messages.warning(request, f'Nu am putut încărca o imagine: {e}')

@login_required
def listing_create_view(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            
            process_images(request, listing)
            
            messages.success(request, 'Anunțul a fost creat cu succes!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        form = ListingForm()
    
    context = {
        'form': form,
        'title': 'Adaugă anunț nou'
    }
    return render(request, 'listings/create_simple.html', context)

@login_required
def listing_update_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save() # save/delete images
            
            messages.success(request, 'Anunțul a fost actualizat!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(queryset=listing.images.all())
    
    context = {
        'form': form,
        'formset': formset,
        'listing': listing,
        'title': f'Editează: {listing.title}'
    }
    return render(request, 'listings/update.html', context)

@login_required
def listing_delete_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Anunțul a fost șters!')
        return redirect('listings:my_listings')
    
    context = {'listing': listing}
    return render(request, 'listings/delete.html', context)

@login_required
def my_listings_view(request):
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    
    paginator = Paginator(listings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'listings/my_listings.html', context)

@login_required
def upload_images_view(request, slug):
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        
        if formset.is_valid():
            for image_form in formset:
                if image_form.cleaned_data and not image_form.cleaned_data.get('DELETE', False):
                    if image_form.cleaned_data.get('image'):  
                        image = image_form.save(commit=False)
                        image.listing = listing
                        image.save()
            
            messages.success(request, 'Imaginile au fost încărcate!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        formset = ListingImageFormSet(queryset=listing.images.all())
    
    context = {
        'listing': listing,
        'formset': formset,
        'title': f'Imagini pentru: {listing.title}'
    }
    return render(request, 'listings/upload_images.html', context)