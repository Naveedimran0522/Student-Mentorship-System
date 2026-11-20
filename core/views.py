from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .forms import *
from .models import *

def home(request):
    return redirect("dashboard") if request.user.is_authenticated else render(request,"core/home.html")
def login_view(request):
    if request.user.is_authenticated: return redirect("dashboard")
    if request.method=="POST":
        user=authenticate(request,username=request.POST.get("username","").strip(),password=request.POST.get("password",""))
        if user: login(request,user); return redirect("dashboard")
        messages.error(request,"Username or password is incorrect.")
    return render(request,"core/login.html")
def logout_view(request):
    if request.method=="POST": logout(request)
    return redirect("login")
def staff_required(user):
    return user.is_staff or user.is_superuser
def can_manage(user):
    return staff_required(user) or hasattr(user,"mentor_profile")
def teacher_students(user):
    qs=StudentProfile.objects.select_related("user","department")
    mentor=getattr(user,"mentor_profile",None)
    if not staff_required(user):
        if mentor: qs=qs.filter(assignment__mentor=mentor)
        else:
            sp=getattr(user,"student_profile",None)
            qs=qs.filter(pk=sp.pk) if sp else qs.none()
    return qs
@login_required
def dashboard(request):
    students=teacher_students(request.user)
    ids=students.values_list("id",flat=True)
    today=timezone.localdate()
    total=students.count()
    attendance=Attendance.objects.filter(student_id__in=ids,date=today)
    fees=FeeRecord.objects.filter(student_id__in=ids)
    return render(request,"core/dashboard.html",{
      "student_count":total,"mentor_count":MentorProfile.objects.count() if staff_required(request.user) else (1 if hasattr(request.user,"mentor_profile") else 0),
      "meeting_count":Meeting.objects.filter(student_id__in=ids).count(),"reports_count":ProgressReport.objects.filter(student_id__in=ids).count(),
      "present_count":attendance.filter(status="PRESENT").count(),"absent_count":attendance.filter(status="ABSENT").count(),
      "fee_total":fees.aggregate(v=Sum("total_amount"))["v"] or 0,"fee_paid":fees.aggregate(v=Sum("paid_amount"))["v"] or 0,"fee_pending":sum((f.total_amount-f.paid_amount for f in fees), start=0),
      "upcoming_meetings":Meeting.objects.filter(student_id__in=ids,scheduled_at__gte=timezone.now(),status="SCHEDULED")[:5]})
@login_required
def students(request):
    qs=teacher_students(request.user)
    q=request.GET.get("q","").strip()
    if q: qs=qs.filter(Q(roll_number__icontains=q)|Q(user__first_name__icontains=q)|Q(user__last_name__icontains=q))
    return render(request,"core/students.html",{"students":qs,"q":q,"can_add":staff_required(request.user) or hasattr(request.user,"mentor_profile")})
@login_required
def add_student(request):
    if not (staff_required(request.user) or hasattr(request.user,"mentor_profile")): raise PermissionDenied
    form=StudentCreateForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        if not staff_required(request.user) and MentorshipAssignment.objects.filter(mentor=request.user.mentor_profile).count()>=40:
            form.add_error(None,"You have reached the 40-student limit.")
        elif User.objects.filter(username=form.cleaned_data["username"]).exists(): form.add_error("username","Username already exists.")
        elif StudentProfile.objects.filter(roll_number=form.cleaned_data["roll_number"]).exists(): form.add_error("roll_number","Roll number already exists.")
        else:
            s=form.save()
            mentor=getattr(request.user,"mentor_profile",None)
            if mentor: MentorshipAssignment.objects.create(student=s,mentor=mentor)
            messages.success(request,"Student profile created.")
            return redirect("students")
    return render(request,"core/form.html",{"form":form,"page_title":"Add student"})
@login_required
def attendance(request):
    qs=Attendance.objects.filter(student__in=teacher_students(request.user))
    form=AttendanceForm(request.POST or None)
    form.fields["student"].queryset=teacher_students(request.user)
    if request.method=="POST" and can_manage(request.user) and form.is_valid():
        obj=form.save(commit=False); obj.marked_by=request.user
        obj.save()
        messages.success(request,"Attendance saved."); return redirect("attendance")
    return render(request,"core/records.html",{"title":"Attendance","form":form,"records":qs.select_related("student__user")[:150],"kind":"attendance","can_add":can_manage(request.user)})
@login_required
def marks(request):
    qs=AcademicMark.objects.filter(student__in=teacher_students(request.user))
    form=MarkForm(request.POST or None); form.fields["student"].queryset=teacher_students(request.user)
    if request.method=="POST" and can_manage(request.user) and form.is_valid():
        form.save(); messages.success(request,"Academic marks saved."); return redirect("marks")
    return render(request,"core/records.html",{"title":"Academic marks","form":form,"records":qs.select_related("student__user")[:150],"kind":"marks","can_add":can_manage(request.user)})
@login_required
def fees(request):
    qs=FeeRecord.objects.filter(student__in=teacher_students(request.user))
    form=FeeForm(request.POST or None); form.fields["student"].queryset=teacher_students(request.user)
    if request.method=="POST" and can_manage(request.user) and form.is_valid():
        form.save(); messages.success(request,"Fee structure saved."); return redirect("fees")
    return render(request,"core/records.html",{"title":"Fee management","form":form,"records":qs.select_related("student__user")[:150],"kind":"fees","can_add":can_manage(request.user)})
@login_required
def fee_payment(request,pk):
    if not can_manage(request.user): raise PermissionDenied
    fee=get_object_or_404(FeeRecord,pk=pk,student__in=teacher_students(request.user))
    form=PaymentForm(request.POST or None)
    if request.method=="POST" and can_manage(request.user) and form.is_valid():
        p=form.save(commit=False); p.fee=fee
        try: p.save()
        except Exception as e: form.add_error(None,str(e))
        else: messages.success(request,"Payment recorded."); return redirect("fees")
    return render(request,"core/form.html",{"form":form,"page_title":f"Record payment · {fee.student}"})
@login_required
def mentors(request):
    return render(request,"core/mentors.html",{"mentors":MentorProfile.objects.select_related("user","department")})
@login_required
def assignments(request):
    qs=MentorshipAssignment.objects.select_related("student__user","mentor__user")
    if not staff_required(request.user):
        m=getattr(request.user,"mentor_profile",None)
        qs=qs.filter(mentor=m) if m else qs.filter(student=getattr(request.user,"student_profile",None))
    return render(request,"core/assignments.html",{"assignments":qs})
@login_required
def meetings(request):
    qs=Meeting.objects.filter(student__in=teacher_students(request.user)).select_related("student__user","mentor__user")
    return render(request,"core/meetings.html",{"meetings":qs})
@login_required
def add_meeting(request):
    form=MeetingForm(request.POST or None); form.fields["student"].queryset=teacher_students(request.user)
    if not staff_required(request.user) and hasattr(request.user,"mentor_profile"): form.fields["mentor"].queryset=MentorProfile.objects.filter(pk=request.user.mentor_profile.pk)
    if request.method=="POST" and can_manage(request.user) and form.is_valid(): form.save(); messages.success(request,"Meeting created."); return redirect("meetings")
    return render(request,"core/form.html",{"form":form,"page_title":"Schedule a meeting"})
@login_required
def progress_reports(request):
    qs=ProgressReport.objects.filter(student__in=teacher_students(request.user)).select_related("student__user","mentor__user")
    form=ProgressReportForm(request.POST or None); form.fields["student"].queryset=teacher_students(request.user)
    if not staff_required(request.user) and hasattr(request.user,"mentor_profile"): form.fields["mentor"].queryset=MentorProfile.objects.filter(pk=request.user.mentor_profile.pk)
    if request.method=="POST" and can_manage(request.user) and form.is_valid(): form.save(); messages.success(request,"Progress report saved."); return redirect("progress")
    return render(request,"core/progress.html",{"reports":qs,"form":form,"can_add":staff_required(request.user) or hasattr(request.user,"mentor_profile")})
