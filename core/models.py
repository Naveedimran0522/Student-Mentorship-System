from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=12, unique=True)
    description = models.TextField(blank=True)
    def __str__(self): return f"{self.name} ({self.code})"

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    roll_number = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="students")
    course = models.CharField(max_length=100, default="BCA")
    semester = models.PositiveSmallIntegerField(default=1)
    academic_year = models.CharField(max_length=20, default="2026-27")
    date_of_birth = models.DateField(null=True, blank=True)
    father_name = models.CharField(max_length=120, blank=True)
    mother_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.roll_number} - {self.user.get_full_name() or self.user.username}"

class MentorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentor_profile")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="mentors")
    designation = models.CharField(max_length=100, default="Faculty Mentor")
    phone = models.CharField(max_length=20, blank=True)
    def __str__(self): return self.user.get_full_name() or self.user.username

class MentorshipAssignment(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name="assignment")
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="assignments")
    assigned_on = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    class Meta: ordering = ["student__roll_number"]
    def clean(self):
        if self.mentor_id and MentorshipAssignment.objects.filter(mentor_id=self.mentor_id).exclude(pk=self.pk).count() >= 40:
            raise ValidationError("A teacher can mentor a maximum of 40 students.")
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self): return f"{self.student} → {self.mentor}"

class Attendance(models.Model):
    STATUS_CHOICES = [("PRESENT","Present"),("ABSENT","Absent"),("LEAVE","Leave")]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")
    remarks = models.CharField(max_length=250, blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ["-date", "student__roll_number"]
        constraints = [models.UniqueConstraint(fields=["student","date"], name="unique_student_attendance_per_day")]
    def __str__(self): return f"{self.student} · {self.date} · {self.status}"

class AcademicMark(models.Model):
    EXAM_TYPES = [("SEMESTER","Previous semester"),("IA","Internal assessment")]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="marks")
    academic_year = models.CharField(max_length=20)
    semester = models.PositiveSmallIntegerField(default=1)
    subject = models.CharField(max_length=120)
    exam_type = models.CharField(max_length=12, choices=EXAM_TYPES)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    exam_date = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=250, blank=True)
    class Meta: ordering = ["-academic_year", "semester", "subject"]
    def clean(self):
        if self.max_marks <= 0 or self.marks_obtained < 0 or self.marks_obtained > self.max_marks:
            raise ValidationError("Marks must be between zero and maximum marks.")
    def __str__(self): return f"{self.student} · {self.subject} · {self.exam_type}"

class FeeRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="fees")
    academic_year = models.CharField(max_length=20)
    fee_type = models.CharField(max_length=100, default="Tuition fee")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["student__roll_number", "fee_type"]
    @property
    def pending_amount(self): return self.total_amount - self.paid_amount
    def clean(self):
        if self.total_amount < 0 or self.paid_amount < 0 or self.paid_amount > self.total_amount:
            raise ValidationError("Paid amount cannot exceed total fee.")
    def __str__(self): return f"{self.student} · {self.fee_type}"

class FeePayment(models.Model):
    fee = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=250, blank=True)
    def clean(self):
        if self.amount <= 0 or (self.fee_id and self.amount > self.fee.pending_amount):
            raise ValidationError("Payment must be positive and cannot exceed pending fee.")
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.fee.paid_amount = sum(p.amount for p in self.fee.payments.all())
        self.fee.save(update_fields=["paid_amount","updated_at"])
    def __str__(self): return f"{self.fee.student} · ₹{self.amount}"

class Meeting(models.Model):
    STATUS_CHOICES = [("SCHEDULED","Scheduled"),("COMPLETED","Completed"),("CANCELLED","Cancelled")]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="meetings")
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="meetings")
    scheduled_at = models.DateTimeField()
    agenda = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="SCHEDULED")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-scheduled_at"]
    def __str__(self): return f"{self.student} — {self.scheduled_at:%d %b %Y}"

class ProgressReport(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="progress_reports")
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="progress_reports")
    academic_score = models.PositiveSmallIntegerField(default=0)
    attendance_percent = models.PositiveSmallIntegerField(default=0)
    strengths = models.TextField(blank=True)
    concerns = models.TextField(blank=True)
    action_plan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Progress: {self.student}"
