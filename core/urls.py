from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactMessageView2,
    ProjectViewSet,
    ReportListAPIView,
    ScanResultViewSet,
    RegisterView,
    DashboardAPIView,
    UserProfileAPIView,
    NotificationSettingsAPIView,
    DisplaySettingsAPIView,
    ApiIntegrationAPIView,
    RegenerateApiKeyAPIView,
    ComplianceSettingsAPIView,
    SecuritySettingsAPIView,
    HelpCenterView,
    ContactMessageView,
    # In views ko aapko views.py mein banana hoga (niche dekhein)
    GoogleLogin,
    LinkedInLogin 
)
from .views import RegisterView, VerifyOTPView 
from .views import ReportDetailAPIView
from .views import RegisterView, VerifyOTPView
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'scan-results', ScanResultViewSet, basename='scan-results')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),

    path('', include(router.urls)),

    path("notifications/", NotificationSettingsAPIView.as_view(), name="notifications"),
    path("display/", DisplaySettingsAPIView.as_view(), name="display"),
    path("apiintegration/", ApiIntegrationAPIView.as_view(), name="apiintegration"),
    path("apiintegration/regenerate/", RegenerateApiKeyAPIView.as_view(), name="regenerate-apikey"),
    path("compliance/", ComplianceSettingsAPIView.as_view(), name="compliance"),
    path("security/", SecuritySettingsAPIView.as_view(), name="security"),
    path("help-center/", HelpCenterView.as_view(), name="help-center"),
    path('contact-message/', ContactMessageView.as_view(), name='contact-message'),
    path('contact-message2/', ContactMessageView2.as_view(), name='contact-message2'),

    # --- SOCIAL AUTH URLS ---
    path('auth/', include('dj_rest_auth.urls')), # Login/Logout/Password reset
    path('auth/registration/', include('dj_rest_auth.registration.urls')), # Registration
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('auth/linkedin/', LinkedInLogin.as_view(), name='linkedin_login'),
    
    # allauth standard urls (for callback)
    path('accounts/', include('allauth.urls')),

# Ye sidebar ke liye saari reports dega
    path('report/', ReportListAPIView.as_view(), name='report-list'),
    
    # Ye specific report ke liye hai
    path('report/<int:report_id>/', ReportDetailAPIView.as_view(), name='report-detail'),
]