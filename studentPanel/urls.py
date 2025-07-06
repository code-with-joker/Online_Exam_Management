from django.urls import path
from . import views

urlpatterns = [
    
    path('generate-fee-receipt/', views.generate_fee_receipt, name='generate_fee_receipt'), # Generate Fee Receipt kaam ka hai
    path('receipt-status/', views.receipt_status, name='receipt_status'),
    path('admin/receipt-request/', views.admin_receipt_requests, name='admin_receipt_requests'),
    path('admin/update-receipt/<int:receipt_id>/<str:action>/', views.update_receipt_status, name='update_receipt_status'),
    path('student/dashboard/', views.student_home, name='student_profile'),
    path('student/admit-card/', views.student_admit_card, name='student_admit_card'),
      path('ac/p/<int:student_id>/', views.generate_admit_pdf, name='generate_admit_pdf'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('download-invoice/<str:transaction_id>/', views.download_invoice, name='download_invoice'),

]
