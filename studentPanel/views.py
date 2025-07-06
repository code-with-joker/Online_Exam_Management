from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from adminPanel.views import PDF
from .models import Student, FeeReceipt
from adminPanel.models import StudentSubject as BackPaper, Subject
from django.contrib.auth.decorators import login_required, user_passes_test
from adminPanel.forms import *
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password
from adminPanel.views import is_student
from django.contrib.auth.models import Group
import uuid
from django.template.loader import get_template
from xhtml2pdf import pisa


@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')

def generate_fee_receipt(request):
    student = get_object_or_404(Student, user=request.user)

    subjects = Subject.objects.filter(semester=student.semester, department=student.branch)
    back_papers = BackPaper.objects.filter(student=student)

    backPaper_count = back_papers.count()

    # Fee logic: ₹200 for 1 or 2 papers, then +₹100 per extra paper
    if backPaper_count == 0:
        backPaper_fee = 0
    elif backPaper_count <= 2:
        backPaper_fee = 200
    else:
        extra_papers = backPaper_count - 2
        backPaper_fee = 200 + (extra_papers * 100)

    total_fee = backPaper_fee  # No normal fee
    last_receipt = FeeReceipt.objects.filter(student=student).order_by('-created_at').first()

    if request.method == "POST":
        if back_papers.exists() and not last_receipt:
            txn_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
            FeeReceipt.objects.create(
                student=student,
                amount=total_fee,
                transaction_id=txn_id,
            )
            messages.success(request, f"Payment submitted. Transaction ID: {txn_id}")
        elif last_receipt:
            messages.info(request, "Payment has already been submitted.")
        else:
            messages.warning(request, "No back papers, no payment required.")

        return redirect('receipt_status')

    context = {
        'student': student,
        'subjects': subjects,
        'back_papers': back_papers,
        'backPaper_fee': backPaper_fee,
        'total_fee': total_fee,
        'last_receipt': last_receipt,
    }
    return render(request, 'studentPanel/fee_receipt.html', context)


def download_invoice(request, transaction_id):
    try:
        payment = get_object_or_404(FeeReceipt, transaction_id=transaction_id)
    except FeeReceipt.DoesNotExist:
        return HttpResponse("Invalid transaction ID", status=404)

    template = get_template('studentPanel/invoice_pdf.html')
    html = template.render({'payment': payment})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{transaction_id}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def receipt_status(request):
    # student = get_object_or_404(Student, user=request.user)
    try:
        student = Student.objects.get(user=request.user)
        latest_receipt = FeeReceipt.objects.filter(student=student).order_by('-created_at').first()
    except Student.DoesNotExist:
        return render(request, 'studentPanel/receipt_status.html')  # Custom error page
     # ✅ Only get approved receipts
    receipt = FeeReceipt.objects.filter(student=student).order_by('-created_at').first()

    context = {'receipt': receipt, 'student': student,
               'latest_receipt': latest_receipt,
               }
    return render(request, 'studentPanel/receipt_status.html', context)


def admin_receipt_requests(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check

    receipts = FeeReceipt.objects.all().order_by('-created_at')
    context = {'receipts': receipts, }
    return render(request, 'studentPanel/admin_receipt_requests.html', context)

# @login_required
def update_receipt_status(request, receipt_id, action):
    receipt = get_object_or_404(FeeReceipt, id=receipt_id)
    # Check if the status has already been set
    if receipt.status in ['approved', 'rejected']:
        # Optionally, show a message saying it's already decided
        messages.success(request, "It's already decided.")

        return redirect('admin_receipt_requests')  # or redirect with a message
    
    if action == "approve":
        receipt.status = 'approved'
    elif action == "reject":
        receipt.status = 'rejected'

    receipt.save()
    return redirect('admin_receipt_requests')



@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def student_home(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        # Redirect to registration or show a message
        return redirect('login')  # Adjust this to your URL name
    return render(request, 'studentPanel/student_profile.html', {
        'student': student,
    })





# ---------------- Student Admit card  ----------------
@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def student_admit_card(request):
    student = get_object_or_404(Student, user=request.user)
    subjects = Subject.objects.filter(semester=student.semester, department=student.branch)
    back_papers = BackPaper.objects.filter(student=student)
    # Get exam details for each subject
    exam_details = []
    for subject in subjects:
        exam = ExamDetail.objects.filter(subject=subject).first()
        exam_date = exam.exam_date.strftime("%d-%m-%Y") if exam else "-"
        exam_time = f"{exam.start_time.strftime('%I:%M %p')} - {exam.end_time.strftime('%I:%M %p')}" if exam else "-"
        
        exam_details.append({
            'subject': subject,
            'exam_date': exam_date,
            'exam_time': exam_time
        })

        # Create a list of back papers with corresponding exam details
    back_paper_details = []
    for back_paper in back_papers:
        exam = ExamDetail.objects.filter(subject=back_paper.subject).first()  # Get the first exam detail for this back paper
        exam_date = exam.exam_date.strftime("%d-%m-%Y") if exam else "-"
        exam_time = f"{exam.start_time.strftime('%I:%M %p')} - {exam.end_time.strftime('%I:%M %p')}" if exam else "-"
        
        back_paper_details.append({
            'subject': back_paper.subject,
            'exam_date': exam_date,
            'exam_time': exam_time
        })


    context = {
        'student': student,
        'subjects': subjects,
        'back_paper_details': back_paper_details,
        'exam_details': exam_details,

    }

    return render(request, 'studentPanel/admit_card.html', context)


# ---------------- Generate Admit Card of student PDF ----------------
@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def generate_admit_pdf(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Fetch StudentSubject entries
    regular_subjects = Subject.objects.filter(semester=student.semester, department=student.branch)
    back_papers = StudentSubject.objects.filter(student=student)


    # pdf = AdmitCardPDF()
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.student_info(student)
    
    if regular_subjects.exists():
        pdf.subject_table(regular_subjects, "Regular Subjects")

    if back_papers.exists():
        pdf.ln(5)  # space between tables
        pdf.subject_table(back_papers, "Back Papers")
    

    pdf.signature_boxes()

    # Output PDF as bytes
    pdf_data = bytes(pdf.output(dest='S'))  # Use bytes here to avoid encode/decode error

    # Return PDF as HTTP response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=admit_card_{student.enrollment}.pdf'
    return response

# ---------------- Student Logout ----------------
@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def student_logout(request):
    logout(request)  # Clears session data
    messages.success(request, "Logged out successfully dude.")
    request.session.flush()  # Extra precaution to clear all session data
    return redirect('login')  # Redirect to student login page





def unified_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Check Student Login (Using the User model's username)
        student = Student.objects.filter(user__username=username).first()  # Filter based on the user username (enrollment number)
        if student and check_password(password, student.user.password):
            login(request, student.user)  # Log in the user
            # Store student ID in session
            request.session['student_id'] = student.id
            messages.success(request, f"Welcome, {student.name}!")  # Display student name
            return redirect('student_profile')  # Redirect to student profile or dashboard
    
        
        # Check if the user is a Django Admin user (from default User model)
        user = User.objects.filter(username=username).first()  # This checks against Django's built-in User model
        if user and check_password(password, user.password):
            
            request.session['admin_id'] = user.id  # You can use 'admin_id' session or modify as per your needs
            messages.success(request, "Admin Login Successful!")
            return redirect('ca')  # Redirect to the Django admin dashboard

        # If login fails
        messages.error(request, "Invalid credentials!")
        return redirect('login')  # Redirect back to the login page

    return render(request, 'studentPanel/login.html')






