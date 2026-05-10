from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static

# JWT AUTH
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

# ==================================================
# FRONTEND URL
# ==================================================
FRONTEND_URL = "https://esccapp.netlify.app"

# ==================================================
# GOOGLE LOGIN SUCCESS HANDLER
# ==================================================
@login_required
def social_login_success(request):
    """
    Google login ke baad JWT tokens generate karega
    aur React frontend dashboard per redirect karega.
    """

    user = request.user

    # Generate JWT Tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Frontend Redirect URL
    target_url = (
        f"{FRONTEND_URL}/dashboard"
        f"?access={access_token}"
        f"&refresh={refresh_token}"
    )

    print(f"\n✅ LOGIN SUCCESS: {user.email}")
    print(f"➡ Redirecting To: {target_url}\n")

    return redirect(target_url)

# ==================================================
# URL PATTERNS
# ==================================================
urlpatterns = [

    # Admin Panel
    path('admin/', admin.site.urls),

    # Core APIs
    path('api/', include('core.urls')),

    # JWT Authentication
    path(
        'api/login/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    # Allauth URLs
    path('accounts/', include('allauth.urls')),

    # Google Login Redirect
    path(
        'accounts/profile/',
        social_login_success,
        name='social_login_success'
    ),
]

# ==================================================
# MEDIA FILES
# ==================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )