from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Department, MentorProfile, StudentProfile, MentorshipAssignment, Attendance, AcademicMark, FeeRecord
from datetime import date
class StudentSystemTests(TestCase):
    def setUp(self):
        self.dept=Department.objects.create(name="Computer Science",code="CS")
        u=User.objects.create_user("teacher",password="Testpass123!")
        self.teacher=MentorProfile.objects.create(user=u,department=self.dept)
    def make_student(self,n):
        u=User.objects.create_user(f"student{n}",password="Testpass123!")
        return StudentProfile.objects.create(user=u,roll_number=f"R{n}",department=self.dept)
    def test_teacher_limit_40(self):
        for n in range(40): MentorshipAssignment.objects.create(student=self.make_student(n),mentor=self.teacher)
        with self.assertRaises(ValidationError): MentorshipAssignment.objects.create(student=self.make_student(41),mentor=self.teacher)
    def test_attendance_unique_per_day(self):
        s=self.make_student(1); Attendance.objects.create(student=s,date=date(2026,1,1))
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): Attendance.objects.create(student=s,date=date(2026,1,1))
    def test_mark_bounds(self):
        s=self.make_student(1); m=AcademicMark(student=s,academic_year="2026-27",semester=1,subject="Math",exam_type="IA",marks_obtained=55,max_marks=50)
        with self.assertRaises(ValidationError): m.full_clean()
    def test_fee_pending(self):
        s=self.make_student(1); f=FeeRecord.objects.create(student=s,academic_year="2026-27",fee_type="Tuition",total_amount=50000,paid_amount=10000)
        self.assertEqual(f.pending_amount,40000)
