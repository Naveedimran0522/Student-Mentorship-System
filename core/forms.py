from django import forms
from django.contrib.auth.models import User
from .models import *

class StudentCreateForm(forms.Form):
    username=forms.CharField(max_length=150)
    password=forms.CharField(widget=forms.PasswordInput)
    first_name=forms.CharField(max_length=150)
    last_name=forms.CharField(required=False)
    email=forms.EmailField(required=False)
    roll_number=forms.CharField(max_length=30)
    department=forms.ModelChoiceField(queryset=Department.objects.all())
    course=forms.CharField(max_length=100, initial="BCA")
    semester=forms.IntegerField(min_value=1, max_value=12, initial=1)
    academic_year=forms.CharField(max_length=20, initial="2026-27")
    date_of_birth=forms.DateField(required=False, widget=forms.DateInput(attrs={"type":"date"}))
    father_name=forms.CharField(required=False)
    mother_name=forms.CharField(required=False)
    phone=forms.CharField(required=False)
    parent_phone=forms.CharField(required=False)
    def save(self):
        d=self.cleaned_data
        u=User.objects.create_user(username=d["username"],password=d["password"],first_name=d["first_name"],last_name=d["last_name"],email=d["email"])
        return StudentProfile.objects.create(user=u,roll_number=d["roll_number"],department=d["department"],course=d["course"],semester=d["semester"],academic_year=d["academic_year"],date_of_birth=d["date_of_birth"],father_name=d["father_name"],mother_name=d["mother_name"],phone=d["phone"],parent_phone=d["parent_phone"])

class AttendanceForm(forms.ModelForm):
    class Meta:
        model=Attendance
        fields=["student","date","status","remarks"]
        widgets={"date":forms.DateInput(attrs={"type":"date"})}
class MarkForm(forms.ModelForm):
    class Meta:
        model=AcademicMark
        fields=["student","academic_year","semester","subject","exam_type","marks_obtained","max_marks","exam_date","remarks"]
        widgets={"exam_date":forms.DateInput(attrs={"type":"date"})}
class FeeForm(forms.ModelForm):
    class Meta:
        model=FeeRecord
        fields=["student","academic_year","fee_type","total_amount","due_date"]
        widgets={"due_date":forms.DateInput(attrs={"type":"date"})}
class PaymentForm(forms.ModelForm):
    class Meta:
        model=FeePayment
        fields=["amount","paid_on","reference","note"]
        widgets={"paid_on":forms.DateInput(attrs={"type":"date"})}
class MeetingForm(forms.ModelForm):
    class Meta:
        model=Meeting
        fields=["student","mentor","scheduled_at","agenda","notes","status"]
        widgets={"scheduled_at":forms.DateTimeInput(attrs={"type":"datetime-local"})}
class ProgressReportForm(forms.ModelForm):
    class Meta:
        model=ProgressReport
        fields=["student","mentor","academic_score","attendance_percent","strengths","concerns","action_plan"]
        widgets={f:forms.Textarea(attrs={"rows":3}) for f in ["strengths","concerns","action_plan"]}
