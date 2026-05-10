from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        
        # SimpleJWT tokens generation
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Check if production or local
        # Referer check ya settings se base URL uthayein
        frontend_url = settings.FRONTEND_URL 
        
        # Final URL with tokens
        target_url = f"{frontend_url}/dashboard?access={access_token}&refresh={refresh_token}"
        
        print(f"🚀 AUTH SUCCESS: {user.email} -> Redirecting to {frontend_url}")
        
        return target_url