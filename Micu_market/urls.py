from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),

    # django allauth urls
    path("accounts/", include("allauth.urls")),
    
    # homepage
    path("", include(("listings.urls", "listings"), namespace="listings")),
    
    # apps
    path("pages/", include(("pages.urls", "pages"), namespace="pages")),
    path("accounts/custom/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("categories/", include(("categories.urls", "categories"), namespace="categories")),
    path("search/", include(("search.urls", "search"), namespace="search")),
    path("chat/", include(("chat.urls", "chat"), namespace="chat")),
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),
    path("favorites/", include(("favorites.urls", "favorites"), namespace="favorites")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
    path("api/", include(("api.urls", "api"), namespace="api")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)