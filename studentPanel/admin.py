from django.contrib import admin
from .models import *
# Register your models here.

# class StudentAdmin(admin.ModelAdmin):
#     list_display = ( 'user', 'enrollment_number', 'semester', 'name', 'semester')
#     search_fields = ('enrollment_number', 'name', 'branch')
#     list_filter = ('branch', 'semester')
# admin.site.register(Student, StudentAdmin)

# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('name', 'semester', 'branch')
#     search_fields = ('name', 'branch')
#     list_filter = ('semester', 'branch')
# admin.site.register(Subject, SubjectAdmin)

class FeeReceiptAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'transaction_id','status', 'created_at')
    search_fields = ('student__name', 'status')
    list_filter = ('status', 'created_at')
admin.site.register(FeeReceipt, FeeReceiptAdmin)

# class BackPaperAdmin(admin.ModelAdmin):
#     list_display = ('student', 'subject', 'original_semester')
#     search_fields = ('student__name', 'subject__name')
#     list_filter = ('original_semester',)
# admin.site.register(BackPaper, BackPaperAdmin)