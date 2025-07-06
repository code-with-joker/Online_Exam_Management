from django.contrib import admin
from .views import *

# Register your models here.
# -------- This is used to show the department in the admin panel. --------
class DepartmentAdmin(admin.ModelAdmin):
    list_display=('code', 'name', 'full_name_branch')
    # search_fields=('code', 'name')
admin.site.register(Department,DepartmentAdmin)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'enrollment', 'name', 'branch', 'semester', 'college', 'email', 'mobile', 'gender', 'father_name', 'mother_name', 'father_mobile', 'blood_group','profile_pic')
admin.site.register(Student, StudentAdmin) 

# ------ This is used to show the institute in the admin panel. -------
class SubjectAdmin(admin.ModelAdmin):
    list_display=('subject_code', 'subject_name', 'semester', 'department')
admin.site.register(Subject,SubjectAdmin)

class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'subject')
admin.site.register(StudentSubject, StudentSubjectAdmin) 

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    # search_fields = ('name', 'subject__name')
    # list_filter = ('subject',)
admin.site.register(Teacher, TeacherAdmin)

class InvigilatorDutyAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'exam', 'venue', 'status')
    # search_fields = ('faculty_name', 'exam__name', 'venue')
    # list_filter = ('exam', 'status')
admin.site.register(InvigilatorDuty, InvigilatorDutyAdmin)

# ------- This is used to show the institute in the admin panel. -------
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'full_name_institute')
    # search_fields = ('name', 'address')
admin.site.register(Institute, InstituteAdmin)    

class ExamDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'exam_date', 'start_time', 'end_time')
    # search_fields = ('name', 'date')
admin.site.register(ExamDetail, ExamDetailAdmin)

class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'date', 'start_time', 'end_time')
    # search_fields = ('name', 'date')
admin.site.register(Exam, ExamAdmin)

