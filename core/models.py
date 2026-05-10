import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

# ================== USER MODEL ==================
class User(AbstractUser):
    ROLE_CHOICES = (
        ('developer', 'Developer'),
        ('student', 'Student'),
        ('admin', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    two_factor_enabled = models.BooleanField(default=False)
    
    # Settings Fields
    organization = models.CharField(max_length=150, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Social Auth & OTP
    social_avatar_url = models.URLField(max_length=500, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True) # <--- YEH ZAROORI HAI
    
    auth_provider = models.CharField(
        max_length=50, 
        default='email',
        choices=[('email', 'email'), ('google', 'google'), ('linkedin', 'linkedin')]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

# ================== PROJECT MODEL (UPDATED) ==================
class Project(models.Model):
    STATUS_CHOICES = (
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    )

    # Naya: Scan modes define kiye hain taake logic sync rahe
    SCAN_MODE_CHOICES = (
        ('standard', 'Standard Analysis'),
        ('deep', 'Deep Forensic Scan'),
    )

    name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    file = models.FileField(upload_to='projects/')
    framework = models.CharField(max_length=100, default='General Standard')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # [ADDED FIELD] Ye field aapke frontend selection ko save karegi
    scan_type = models.CharField(
        max_length=20, 
        choices=SCAN_MODE_CHOICES, 
        default='standard'
    )

    def __str__(self):
        return f"{self.name} - {self.framework} ({self.scan_type})"

# ================== SCAN RESULT MODEL ==================
class ScanResult(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scan_results')
    ethical_score = models.IntegerField(default=0)
    security_score = models.IntegerField(default=0)
    
    # Isme hum detail vulnerabilities, line numbers aur AI suggestions rakhenge
    details = models.JSONField(default=dict) 
    
    # Nayi Field: Direct AI ki taraf se mashwara
    ai_recommendation = models.TextField(blank=True, null=True)
    
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan for {self.project.name} - {self.scanned_at}"

# ================== FRAMEWORK MODEL ==================
class Framework(models.Model):
    title = models.CharField(max_length=100)
    value = models.IntegerField(default=0)  # % compliance

    def __str__(self):
        return self.title


# ================== DASHBOARD STATS MODEL ==================
class Stats(models.Model):
    projects_scanned = models.IntegerField(default=0)
    issues_detected = models.IntegerField(default=0)
    compliance_score = models.IntegerField(default=0)

    ethical_score = models.IntegerField(default=0)
    cybersecurity_score = models.IntegerField(default=0)

    ethical_issues = models.IntegerField(default=0)
    security_weaknesses = models.IntegerField(default=0)

    def __str__(self):
        return "Dashboard Stats"


# ================== CHART MODELS ==================

# 🟡 Compliance Trend Chart
class ComplianceTrend(models.Model):
    # 👇 Ye line lazmi add karein taaki data user-specific ho
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trends', null=True)
    month = models.CharField(max_length=10)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.user.username if self.user else 'Global'} - {self.month}"

# 🔴 Issues by Category Chart
class IssueCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    category_name = models.CharField(max_length=255)
    issue_count = models.IntegerField(default=0)

# 🔵 Framework Compliance (Donut Chart)
class FrameworkCompliance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='framework_scores') # 👈 Ye line add karein
    framework = models.CharField(max_length=50)
    score = models.IntegerField()
# ================== NOTIFICATION SETTINGS ==================
class NotificationSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_settings"
    )

    email_notifications = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=False)
    system_updates = models.BooleanField(default=True)
    weekly_reports = models.BooleanField(default=False)

    def __str__(self):
        return f"Notifications - {self.user.email}"


# ================== DISPLAY SETTINGS MODEL ==================
class DisplaySettings(models.Model):
    THEME_CHOICES = (
        ('dark', 'Dark'),
        ('light', 'Light'),
        ('system', 'System'),
    )

    FONT_CHOICES = (
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="display_settings")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')
    font_size = models.CharField(max_length=10, choices=FONT_CHOICES, default='medium')

    def __str__(self):
        return f"{self.user.email} Display Settings"


# ================== API INTEGRATION MODEL ==================
class ApiIntegration(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_integration"
    )
    api_key = models.CharField(max_length=255, unique=True, blank=True)
    webhook_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = "sk_live_" + secrets.token_hex(24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} API Integration"



# ================== API COMPLIANCESSETTINGS MODEL ==================
class ComplianceSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="compliance_settings"
    )

    iso_27001 = models.BooleanField(default=False)
    gdpr = models.BooleanField(default=False)
    hipaa = models.BooleanField(default=False)
    soc2 = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Compliance Settings - {self.user.email}"


#___________password


class SecuritySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    two_factor_enabled = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

#---------------helpcenter

# HERO SECTION
class HelpHero(models.Model):
    title = models.CharField(max_length=200, default="ESCC Help & Support Center")
    subtitle = models.TextField(default="Find answers, guides, and support for your compliance checking needs")
    search_placeholder = models.CharField(max_length=200, default="Search for help topics, documentation, or FAQs...")
    quick_buttons = models.JSONField(default=list)  # ["Getting Started", "Upload Files", ...]

    def __str__(self):
        return self.title

# DOCUMENTATION / GUIDES
class Documentation(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

# FAQ
class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

# SUPPORT RESOURCES
class SupportResource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

# RELEASE NOTES
class ReleaseNote(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-release_date", "order"]

# CONTACT MESSAGES
class ContactMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"

#guest

# GUEST CONTACT MESSAGES
class GuestContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Guest: {self.name} - {self.subject}"
#______________report
class Report(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        null=True,    # Allow null for old rows
        blank=True    # Allow blank in forms
    )
    report_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    compliance_score = models.IntegerField()
    total_issues = models.IntegerField()
    critical_issues = models.IntegerField()
    high_issues = models.IntegerField()
    medium_issues = models.IntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Issue(models.Model):
    LEVEL_CHOICES = [
        ("CRITICAL", "Critical"),
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
    ]
    report = models.ForeignKey(Report, related_name="issues", on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Ye do nayi fields add karein:
    line_number = models.CharField(max_length=50, default="N/A", blank=True, null=True)
    file_path = models.CharField(max_length=500, default="N/A", blank=True, null=True)

    def __str__(self):
        return f"{self.level} - {self.title}"
class Progress(models.Model):
    report = models.ForeignKey(Report, related_name="progresses", on_delete=models.CASCADE)
    framework = models.CharField(max_length=50)
    value = models.IntegerField()  # store as 0-100

    def __str__(self):
        return f"{self.framework} - {self.value}%"

class HistoricalReport(models.Model):
    report = models.ForeignKey(Report, related_name="history", on_delete=models.CASCADE)
    date = models.DateField()
    score = models.IntegerField()

    def __str__(self):
        return f"{self.date} - {self.score}"

class Recommendation(models.Model):
    report = models.ForeignKey(Report, related_name="recommendations", on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text[:50]




