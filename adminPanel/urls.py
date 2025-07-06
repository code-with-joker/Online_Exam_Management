from django.urls import path
from . import views

urlpatterns = [
    path('', views.unified_login, name='login'),
    path('admin', views.admin_dashboard, name='admin'),
    # ----------------------- Department Management -----------------------
    path('admin/manage-departments/', views.manage_department_view, name='manage_departments'),
    path('delete_department/<int:dept_id>/', views.delete_department, name='delete_department'),
    # ----------------------- Institute Management -----------------------
    path('admin/manage_institute/', views.manage_institute_view, name='manage_institute'),
    path('admin/delete-institute/<int:inst_id>/', views.delete_institute_view, name='delete_institute'),
    # ----------------------- Course Management -----------------------
    path('admin/manage_subjects/', views.manage_subjects, name='manage_subjects'),
    path('delete_subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    # ----------------------- Student Management -----------------------
    path('admin/students_list/', views.student_list, name='student_list'),
    path('admin/delete_students_list/<int:student_id>/', views.delete_student_list, name='delete_students_list'),
    # ----------------------- Student Subject Management -----------------------
    path('admin/student/subject_back/', views.manage_students_subjects, name='manage_student_subjects'),
    path('admin/student/subject_back/<int:student_id>/delete/', views.delete_students_subjects, name='delete_students_subjects'),
    path('admin/esp/', views.export_subjects_pdf, name='export_subjects_pdf'),
    # ------------------------ Invigilator duty details -------------------------
    path('admin/invigilator-duty/detail/', views.invigilator_duties_detail, name='duty_detail'),
    path('admin/delete-teacher/<int:teacher_id>/', views.delete_teacher_duty, name='delete_teacher_duty'),
    path('admin/delete-exams/<int:examDetail_id>/', views.delete_exam_detail, name='delete_exam_detail'),

    path('admin/delete-exam/<int:exam_id>/', views.delete_exam_duty, name='delete_exam_duty'),
    path('admin/delete-venue/<int:venue_id>/', views.delete_venue_duty, name='delete_venue_duty'),

    path('admin/invigilator-duty/', views.invigilator_duties_view, name='invigilator_duties'),
    path('admin/delete-duty/<int:duty_id>/', views.delete_invigilator_duty, name='delete_invigilator_duty'),

    path('admin/delete-all-duties/', views.delete_all_duties_view, name='delete_all_duties'),
    path('admin/invigilator/duty/export/pdf/', views.export_duties_pdf, name='export_duties_pdf'),
    path('admin/manage-exams/', views.manage_exam_details, name='manage_exam_details'),
    # --------------------------- Student profile Update ------------------
    path('admin/update-profile/', views.update_student_profile, name='update_student_profile'),
    path('admin/delete_receipt/<int:receipt_id>/', views.delete_receipt, name='delete_receipt'),
    # --------------------------- Admin Logout -------------
    path('admin/admin_logout/', views.admin_logout, name='admin_logout'),


    





]