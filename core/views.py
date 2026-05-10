import csv
import io
import json
import os
import subprocess
import logging
import sys
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Avg, Count
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

# Logger setup
logger = logging.getLogger(__name__)
User = get_user_model()

from .models import (
    Framework, HistoricalReport, Issue, Progress, Project, Recommendation, ScanResult, FrameworkCompliance, IssueCategory,
    ComplianceTrend, NotificationSettings, DisplaySettings, ApiIntegration,
    ComplianceSettings, SecuritySettings, HelpHero, Documentation, FAQ, 
    SupportResource, ReleaseNote, ContactMessage, Report
)
from .serializers import (
    FrameworkSerializer, ProjectSerializer, ScanResultSerializer, 
    RegisterSerializer, SecuritySettingsSerializer, UserSerializer,
    FrameworkComplianceSerializer, IssueCategorySerializer, ComplianceTrendSerializer,
    NotificationSettingsSerializer, DisplaySettingsSerializer, ApiIntegrationSerializer,
    ComplianceSettingsSerializer, HelpHeroSerializer, DocumentationSerializer, 
    FAQSerializer, SupportResourceSerializer, ReleaseNoteSerializer, 
    ContactMessageSerializer, 
)

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import random
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # User save karein (Inactive by default for security)
        user = serializer.save()
        user.is_active = False 
        
        # OTP generate aur save karein
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.save()
        
        # Email functionality
        subject = "Verify Your Account - ESCC"
        message = f"Hi {user.username},\n\nYour verification code is: {otp}\n\nThank you for joining Ethical Software Compliance."
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")

@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp_received = str(request.data.get('otp', '')).strip()

        try:
            user = User.objects.get(email=email)
            
            # OTP Check
            if user.otp and user.otp == otp_received:
                user.is_active = True
                user.otp = ""  # Ek baar use hone ke baad khatam
                user.save()
                return Response({"detail": "Account verified successfully!"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        return Response(UserSerializer(request.user).data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
 #project scan   
import uuid
import json
import subprocess
import os
import sys
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(uploaded_by=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        # 1. Frontend se framework aur scan_mode lena
        framework_name = self.request.data.get('framework', 'GDPR')
        selected_scan_mode = self.request.data.get('scan_type', 'standard') 
        
        # 2. Initial Save
        project = serializer.save(
            uploaded_by=self.request.user, 
            framework=framework_name,
            scan_type=selected_scan_mode,
            status='Pending'
        )
        
        try:
            # 3. AI Engine setup
            file_path = project.file.path
            script_path = os.path.join(settings.BASE_DIR, 'ai_engine', 'predict.py')
            
            # 4. AI Script run (Arguments update kiye gaye hain predict.py ke mutabiq)
            # Order: [python, script, file_path, framework, scan_mode]
            result = subprocess.run(
                [sys.executable, script_path, file_path, framework_name, selected_scan_mode],
                capture_output=True, text=True, timeout=180
            )

            if result.returncode == 0:
                ai_output = json.loads(result.stdout)
                
                # Data extract karna
                e_score = float(ai_output.get('ethical_score', 0))
                s_score = float(ai_output.get('security_score', 0))
                avg_score = (e_score + s_score) / 2
                details = ai_output.get('details', {})
                
                crit = int(details.get('critical', 0))
                high = int(details.get('high', 0))
                med = int(details.get('medium', 0))
                total = crit + high + med

                # 5. SCANRESULT SAVE
                ScanResult.objects.create(
                    project=project,
                    ethical_score=e_score,
                    security_score=s_score,
                    details=ai_output 
                )

                # 6. REPORT GENERATION
                report = Report.objects.create(
                    user=self.request.user, 
                    report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
                    title=f"Scan: {project.name}",
                    description=f"{selected_scan_mode.upper()} Audit for {framework_name}",
                    compliance_score=int(avg_score),
                    total_issues=total,
                    critical_issues=crit,
                    high_issues=high,
                    medium_issues=med
                )
                 # Updated Loop
                vulnerabilities = ai_output.get('vulnerabilities', [])
                for v in vulnerabilities:
                    Issue.objects.create(
                        report=report,
                        level=v.get('severity', 'MEDIUM').upper(),
                        title=v.get('type', 'Security Finding'),
                        description=v.get('message', 'Potential risk detected.'),
                        # ✅ Naya data yahan add karein:
                        line_number=str(v.get('line', 'N/A')), 
                        file_path=v.get('file', 'N/A')
                    )

                # 8. ANALYTICS & TRENDS
                Progress.objects.create(
                    report=report, 
                    framework=framework_name, 
                    value=int(avg_score)
                )
                
                Recommendation.objects.create(
                    report=report,
                    text=f"Mode: {selected_scan_mode}. {framework_name} focus: Detected {crit} critical vulnerabilities."
                )

                HistoricalReport.objects.create(
                    report=report, 
                    date=timezone.now().date(), 
                    score=int(avg_score)
                )

                ComplianceTrend.objects.create(
                    user=self.request.user,
                    month=timezone.now().strftime("%d %b, %H:%M"), 
                    score=int(avg_score)
                )
                
                project.status = 'Completed'
                print(f"✅ Success: {framework_name} ({selected_scan_mode}) completed.")
                
            else:
                print(f"❌ AI Script Error: {result.stderr}")
                project.status = 'Failed'

        except Exception as e:
            print(f"❌ ViewSet Error: {str(e)}")
            project.status = 'Failed'
        
        project.save()
# ================== DASHBOARD API (DATOS PARA CHARTS) ==================
class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        projects = Project.objects.filter(uploaded_by=user)
        scans = ScanResult.objects.filter(project__uploaded_by=user).select_related('project')

        # 1. Agregación de Scores
        agg = scans.aggregate(
            ethical_avg=Avg("ethical_score"),
            security_avg=Avg("security_score")
        )
        eth_avg = round(agg.get("ethical_avg") or 0, 2)
        sec_avg = round(agg.get("security_avg") or 0, 2)
        total_compliance = round((eth_avg + sec_avg) / 2, 2)

        # 2. Contador de Vulnerabilidades
        crit = high = med = 0
        for scan in scans:
            d = scan.details.get("details", {}) if isinstance(scan.details, dict) else {}
            crit += d.get("critical", 0)
            high += d.get("high", 0)
            med += d.get("medium", 0)

       # --- Dashboard Logic (Backend) ---

        framework_data = []
        # Sirf top 6 latest projects fetch karna
        for p in projects.order_by('-id')[:6]:
            latest_scan = scans.filter(project=p).first()
            
            # Score calculation
            if latest_scan:
                avg_score = round((latest_scan.ethical_score + latest_scan.security_score) / 2, 1)
            else:
                avg_score = 0

            framework_data.append({
                "id": p.id,
                "name": p.name,                # Project ka naam (e.g. "Alpha App")
                "framework": p.framework,      # Framework (e.g. "NIST", "OWASP")
                "scan_type": p.scan_type,      # 'deep' ya 'standard' (Card color ke liye critical hai)
                "score": avg_score,
                "status": p.status,
                "description": f"AI Audit for {p.name}",
                "date": p.created_at.strftime("%d %b") if hasattr(p, 'created_at') else ""
            })
        # --- CAMBIO AQUÍ: Incluir datos del usuario ---
        # Si no tienes UserSerializer, puedes usar: 
        # "user": {"username": user.username, "first_name": user.first_name}
        
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,  # <--- Added
                "last_name": user.last_name,    # <--- Added
                "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email
            },
            "stats": {
                "projects_scanned": projects.count(),
                "issues_detected": crit + high + med,
                "critical": crit,
                "high": high,
                "medium": med,
                "compliance_score": total_compliance,
                "ethical_score": eth_avg,
                "cybersecurity_score": sec_avg,
            },
            "projects": ProjectSerializer(projects.order_by('-id')[:5], many=True).data,
            "frameworks": framework_data if framework_data else [{"name": "No Data", "score": 0}],
            "charts": {
                "issues_by_category": [
                    {"category_name": "Critical", "issue_count": crit},
                    {"category_name": "High", "issue_count": high},
                    {"category_name": "Medium", "issue_count": med},
                ],
                "compliance_trend": ComplianceTrendSerializer(
                    ComplianceTrend.objects.filter(user=user).order_by('id'), 
                    many=True
                ).data
            }
        })
    permission_classes = [IsAuthenticated]
# ================== SETTINGS & INTEGRATIONS ==================
class NotificationSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        settings, _ = NotificationSettings.objects.get_or_create(user=request.user)
        return Response(NotificationSettingsSerializer(settings).data)
    def post(self, request):
        settings, _ = NotificationSettings.objects.get_or_create(user=request.user)
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Preferences updated"})

class DisplaySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        settings, _ = DisplaySettings.objects.get_or_create(user=request.user)
        return Response(DisplaySettingsSerializer(settings).data)
    def patch(self, request):
        settings, _ = DisplaySettings.objects.get_or_create(user=request.user)
        serializer = DisplaySettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ApiIntegrationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        obj, _ = ApiIntegration.objects.get_or_create(user=request.user)
        return Response(ApiIntegrationSerializer(obj).data)
    def patch(self, request):
        obj, _ = ApiIntegration.objects.get_or_create(user=request.user)
        serializer = ApiIntegrationSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class RegenerateApiKeyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        obj, _ = ApiIntegration.objects.get_or_create(user=request.user)
        obj.api_key = "sk_live_" + secrets.token_hex(24)
        obj.save()
        return Response({"api_key": obj.api_key})

class ComplianceSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        obj, _ = ComplianceSettings.objects.get_or_create(user=request.user)
        return Response(ComplianceSettingsSerializer(obj).data)
    def put(self, request):
        obj, _ = ComplianceSettings.objects.get_or_create(user=request.user)
        serializer = ComplianceSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class SecuritySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        settings, _ = SecuritySettings.objects.get_or_create(user=request.user)
        return Response(SecuritySettingsSerializer(settings).data)
    def put(self, request):
        settings, _ = SecuritySettings.objects.get_or_create(user=request.user)
        serializer = SecuritySettingsSerializer(settings, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True})
        return Response(serializer.errors, status=400)

# ================== HELP CENTER ==================
class HelpCenterView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        hero = HelpHero.objects.first()
        hero_data = HelpHeroSerializer(hero).data if hero else {}
        return Response({
            "hero": hero_data,
            "documentation": DocumentationSerializer(Documentation.objects.all(), many=True).data,
            "faq": FAQSerializer(FAQ.objects.all(), many=True).data,
            "support": SupportResourceSerializer(SupportResource.objects.all(), many=True).data,
            "releases": ReleaseNoteSerializer(ReleaseNote.objects.all(), many=True).data,
        })

class ContactMessageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        ContactMessage.objects.create(user=request.user, subject=request.data.get("subject"), message=request.data.get("message"))
        send_mail(
            subject=f"New Support Request: {request.data.get('subject')}",
            message=f"From: {request.user.email}\n\n{request.data.get('message')}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
        )
        return Response({"success": True})
    

#-------------------------contact
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser
from django.conf import settings
from .models import GuestContactMessage # Naya model use karein

class ContactMessageView2(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            name = request.data.get("name")
            email = request.data.get("email")
            subject = request.data.get("subject")
            message = request.data.get("message")

            # 1. Database mein save karein
            GuestContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )

            # 2. EMAIL TO ADMIN (Plain Text)
            admin_subject = f"New Contact Form Submission: {subject}"
            admin_msg = f"User Name: {name}\nUser Email: {email}\nSubject: {subject}\n\nMessage:\n{message}"
            
            # fail_silently=True taaki agar SMTP error ho toh app crash na ho
            from django.core.mail import send_mail
            send_mail(admin_subject, admin_msg, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL], fail_silently=True)

            # 3. THANK YOU EMAIL TO USER (HTML Template)
            user_subject = "We received your message! - Ethical Software Compliance"
            context = {'name': name}
            
            # HTML Template ko load karein
            html_content = render_to_string('emails/thank_you.html', context)
            text_content = strip_tags(html_content) # Fallback text

            msg = EmailMultiAlternatives(user_subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)

            return Response({"success": True, "message": "Message sent successfully!"})

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"success": False, "message": "Server error. Please try again later."}, status=500)


 # ================== SCAN RESULT API ==================
class ScanResultViewSet(viewsets.ModelViewSet):
    serializer_class = ScanResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ScanResult.objects.filter(project__uploaded_by=self.request.user)       
    





from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "https://esccapp.netlify.app" # Aapka React URL
    client_class = OAuth2Client

class LinkedInLogin(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter
    callback_url = "https://esccapp.netlify.app"
    client_class = OAuth2Client    


#reports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Report
from .serializers import ReportSerializer

# 1. Sidebar ke liye: User ki saari reports ki list
class ReportListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Filter by user taake har koi apni report dekhe
        reports = Report.objects.filter(user=request.user).order_by('-generated_at')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 2. Specific Report ke liye (Click karne par)
class ReportDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_id=None):
        try:
            user_reports = Report.objects.filter(user=request.user)
            if report_id:
                # Specific ID wali report
                report = user_reports.get(id=report_id) # ya report_id=report_id agar model me field hai
            else:
                # Latest report
                report = user_reports.latest("generated_at")

            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found or access denied"},
                status=status.HTTP_404_NOT_FOUND
            )

class LatestUserReportView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Isme filter pehle se tha, lekin error handling ke liye Try/Except ya 404 zaroori hai
        try:
            return Report.objects.filter(user=self.request.user).latest("generated_at")
        except Report.DoesNotExist:
            return None