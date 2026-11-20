from django.contrib import admin
from .models import Department, StudentProfile, MentorProfile, MentorshipAssignment, Meeting, ProgressReport, Attendance, AcademicMark, FeeRecord, FeePayment
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display=("name","code"); search_fields=("name","code")
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display=("roll_number","user","academic_year","department","course","semester","parent_phone")
    list_filter=("academic_year","department","course","semester")
    search_fields=("roll_number","user__first_name","user__last_name","father_name","mother_name","parent_phone")
@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display=("user","department","designation","phone")
@admin.register(MentorshipAssignment)
class MentorshipAssignmentAdmin(admin.ModelAdmin):
    list_display=("student","mentor","assigned_on"); list_filter=("mentor",)
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display=("student","date","status","marked_by"); list_filter=("date","status"); search_fields=("student__roll_number","student__user__first_name")
@admin.register(AcademicMark)
class AcademicMarkAdmin(admin.ModelAdmin):
    list_display=("student","academic_year","semester","subject","exam_type","marks_obtained","max_marks"); list_filter=("academic_year","semester","exam_type")
@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display=("student","academic_year","fee_type","total_amount","paid_amount","pending_amount")
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display=("fee","amount","paid_on","reference")
@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display=("student","mentor","scheduled_at","status"); list_filter=("status","mentor")
@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display=("student","mentor","academic_score","attendance_percent","created_at")
