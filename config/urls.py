from django.contrib import admin
from django.urls import path
from core import views
urlpatterns=[
 path("admin/",admin.site.urls),path("",views.home,name="home"),path("login/",views.login_view,name="login"),path("logout/",views.logout_view,name="logout"),
 path("dashboard/",views.dashboard,name="dashboard"),path("students/",views.students,name="students"),path("students/add/",views.add_student,name="add_student"),
 path("attendance/",views.attendance,name="attendance"),path("marks/",views.marks,name="marks"),path("fees/",views.fees,name="fees"),path("fees/<int:pk>/payment/",views.fee_payment,name="fee_payment"),
 path("mentors/",views.mentors,name="mentors"),path("assignments/",views.assignments,name="assignments"),path("meetings/",views.meetings,name="meetings"),path("meetings/add/",views.add_meeting,name="add_meeting"),path("progress/",views.progress_reports,name="progress")]
