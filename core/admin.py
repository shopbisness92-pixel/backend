from django.contrib import admin
from .models import (
    User,
    Project,
    ScanResult,
    Framework,
    Stats,
    IssueCategory,
    ComplianceTrend,
    FrameworkCompliance,
    # Help Center Models
    HelpHero,
    Documentation,
    FAQ,
    SupportResource,
    ReleaseNote,
    ContactMessage,
    # ===== New Reports Models =====
    Report,
    Issue,
    Progress,
    HistoricalReport,
    Recommendation,
)

# =================== USER ===================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email")
    list_filter = ("role", "is_staff", "is_active")

# =================== PROJECT ===================
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    # 'framework' ko yahan shamil karein
    list_display = ("name", "uploaded_by", "framework", "status", "uploaded_at") 
    search_fields = ("name", "uploaded_by__username", "framework")
    list_filter = ("status", "uploaded_at", "framework")
    readonly_fields = ("uploaded_at",)
    ordering = ("-uploaded_at",)

# =================== SCAN RESULT ===================
@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ("project", "ethical_score", "security_score", "scanned_at")
    search_fields = ("project__name",)
    list_filter = ("project", "scanned_at")
    readonly_fields = ("scanned_at",)
    ordering = ("-scanned_at",)

# =================== FRAMEWORK ===================
@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ("title", "value")
    search_fields = ("title",)

# =================== STATS ===================
@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = (
        "projects_scanned",
        "issues_detected",
        "compliance_score",
        "ethical_score",
        "cybersecurity_score",
        "ethical_issues",
        "security_weaknesses",
    )

# =================== ISSUE CATEGORY ===================
@admin.register(IssueCategory)
class IssueCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'issue_count')

# =================== COMPLIANCE TREND ===================
@admin.register(ComplianceTrend)
class ComplianceTrendAdmin(admin.ModelAdmin):
    list_display = ("month", "score")
    list_filter = ("month",)

# =================== FRAMEWORK COMPLIANCE ===================
@admin.register(FrameworkCompliance)
class FrameworkComplianceAdmin(admin.ModelAdmin):
    list_display = ("framework", "score")

# =================== HELP CENTER MODELS ===================
@admin.register(HelpHero)
class HelpHeroAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle")
    fields = ("title", "subtitle", "search_placeholder", "quick_buttons")

@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "order")
    list_editable = ("order",)
    ordering = ("order",)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order")
    list_editable = ("order",)
    ordering = ("order",)

@admin.register(SupportResource)
class SupportResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)
    ordering = ("order",)

@admin.register(ReleaseNote)
class ReleaseNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "order")
    list_editable = ("order",)
    ordering = ("-release_date", "order")

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "subject", "message")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

# =================== REPORTS MODELS ===================
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_id", "compliance_score", "total_issues", "generated_at")
    search_fields = ("title", "report_id")
    readonly_fields = ("generated_at",)
    ordering = ("-generated_at",)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "report")
    list_filter = ("level",)
    search_fields = ("title", "report__title")

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("framework", "value", "report")
    list_filter = ("framework",)
    search_fields = ("framework", "report__title")

@admin.register(HistoricalReport)
class HistoricalReportAdmin(admin.ModelAdmin):
    list_display = ("date", "score", "report")
    search_fields = ("report__title",)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("text", "report")
    search_fields = ("text", "report__title")



from .models import GuestContactMessage

@admin.register(GuestContactMessage)
class GuestContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')