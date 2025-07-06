from datetime import datetime
from collections import defaultdict
import random
from django.core.exceptions import ValidationError
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from fpdf import FPDF
from django.contrib.auth.decorators import login_required, user_passes_test
from studentPanel.models import FeeReceipt
from .views import *
from .forms import *
from django.contrib import messages
from django.db.models import Q
from django.db import DatabaseError, IntegrityError
from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, login, logout
from PIL import Image

# from student.models import StudentPayment

# Create your views here.


# Check if the user is a student
def is_student(user):
    return user.groups.filter(name='Student').exists()

def admin_dashboard(request):
    student_count = Student.objects.count()
    teacher_count = Teacher.objects.count()
    backpaper_student_count = StudentSubject.objects.values('student').distinct().count()
    # Student distribution by branch
    branches = Student.objects.values_list('branch__name', flat=True).distinct()
    branch_labels = list(branches)
    branch_counts = [Student.objects.filter(branch__name=branch).count() for branch in branch_labels]

    # Number of subjects per semester
    semesters = Subject.objects.values_list('semester', flat=True).distinct()
    semester_labels = sorted(set(semesters))
    subject_counts = [Subject.objects.filter(semester=sem).count() for sem in semester_labels]

    reminders = []
    # Example condition-based reminders

    pending_payments = FeeReceipt.objects.filter(status='pending').count()
    if pending_payments > 0:
        reminders.append(f"{pending_payments} student payment(s) pending")

    # Recent activities
    recent_students = Student.objects.all().order_by('-id')[:5]
    recent_teachers = Teacher.objects.all().order_by('-id')[:5]

    return render(request, 'adminPanel/index.html', {
        'student_count': student_count,
        'teacher_count': teacher_count,
        'backpaper_student_count': backpaper_student_count,
        'branch_labels': branch_labels,
        'branch_counts': branch_counts,
        'semester_labels': semester_labels,
        'subject_counts': subject_counts,
        'reminders': reminders,
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
    })

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

            # Check Admin Login (Using custom Admin model)
            # admin = Admin.objects.filter(username=username).first()
            # if admin and check_password(password, admin.password):
            #     request.session['admin_id'] = admin.id
            #     messages.success(request, "Admin Login Successful!")
            #     return redirect('ca')  # Redirect to admin dashboard
            
            # Check if the user is a Django Admin user (from default User model)
            user = User.objects.filter(username=username).first()  # This checks against Django's built-in User model
            if user and check_password(password, user.password):
                
                request.session['admin_id'] = user.id  # You can use 'admin_id' session or modify as per your needs
                messages.success(request, "Admin Login Successful!")
                return redirect('admin')  # Redirect to the Django admin dashboard

            # If login fails
            messages.error(request, "Invalid credentials!")
            return redirect('login')  # Redirect back to the login page

        return render(request, 'studentPanel/login.html')
        # return render(request, 'adminPanel/index.html')

# ----------------------- Department Management -----------------------

def manage_department_view(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    if request.method == 'POST':
        try:
            form = DepartmentForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Department added successfully!")
                return redirect('manage_departments')
            else:
                # If form is invalid, display all errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('manage_departments')

    else:
        form = DepartmentForm()

    departments = Department.objects.all().order_by('-id')

    return render(request, 'adminPanel/manage_departments.html', {
        'form': form,
        'departments': departments,
    })

def delete_department(request, dept_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    # department = Department.objects.get(id=dept_id)
    department = get_object_or_404(Department, id=dept_id)
    dept_name = department.name
    # Get students related to this department
    related_students = Student.objects.filter(branch=department)

    for student in related_students:
        # Delete user if linked
        if student.user:
            # Remove from group if needed
            student.user.groups.clear()
            student.user.delete()

        # Delete student (if not automatically handled)
        student.delete()
    department.delete()
    messages.error(request, f"Department '{dept_name}' deleted successfully ❌")
    return redirect('manage_departments')
# ----------------------- End of Department Management -----------------------

# ----------------------- Institute Management -----------------------

def manage_institute_view(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    if request.method == 'POST':
        try:
            form = InstituteForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Institute added successfully!")
                return redirect('manage_institute')
            else:
                # If the form is invalid, display errors for each field
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
        except Exception as e:
            # Catch unexpected errors and display a general error message
            messages.error(request, f"An error occurred: {str(e)}")
            print(e)

            return redirect('manage_institute')

    else:
        form = InstituteForm()

    # Fetch all institutes in reverse order (newest first)
    institutes = Institute.objects.all().order_by('-id')

    return render(request, 'adminPanel/manage_institute.html', {
        'form': form,
        'institutes': institutes,
    })

def delete_institute_view(request, inst_id):
        if not request.session.get('admin_id'):
            return redirect('login')  # Staff check
        try:
            institute = Institute.objects.get(id=inst_id)
            # Get all students linked to the institute
            related_students = Student.objects.filter(college=institute)

            # If students are linked, delete them first
            if related_students.exists():
                for student in related_students:
                    # Remove the student from groups
                    if student.user:
                        student.user.groups.clear()
                        student.user.delete()

                    # Delete the student record
                    student.delete()
            institute.delete()
            messages.success(request, "Institute deleted successfully!")
        except Institute.DoesNotExist:
            messages.error(request, "Institute not found.")
        
        return redirect('manage_institute')
# ----------------------- End of Institute Management -----------------------

# ----------------------- Subject Management -----------------------

def manage_subjects(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Subject added successfully!')
                return redirect('manage_subjects')
            except IntegrityError:
                messages.error(request, 'Subject with this code already exists.')
        else:
            # If the form is not valid, show a general error message
            messages.error(request, 'Please correct the errors below.')
            
            # Ensure that any validation errors are shown for the fields
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = SubjectForm()

    subjects = Subject.objects.all().order_by('-id')
    return render(request, 'adminPanel/manage_subjects.html', {'form': form, 'subjects': subjects})

def delete_subject(request, subject_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, f'Subject "{subject.subject_name}" deleted successfully!')
    return redirect('manage_subjects')  # ya jis page pe redirect karna hai
# ----------------------- End of Subject Management -----------------------

# ----------------------- Student Management -----------------------

def student_list(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    data = Student.objects.all().order_by('-id')

    if request.method == 'POST':
        form = StudentsForm(request.POST)
        try:
            if form.is_valid():
                # Cleaned data will automatically be available after validation
                username = form.cleaned_data['enrollment'].strip()
                name = form.cleaned_data['name'].strip()
                # branch = form.cleaned_data['branch']
                branch =  request.POST.get('branch')
                branch_instance = Department.objects.get(id=branch)
                semester = form.cleaned_data['semester']
                college = request.POST.get('college')
                college_instance = Institute.objects.get(id=college)
                # Check if the enrollment number already exists in the Student model
                if Student.objects.filter(enrollment=username).exists():
                    messages.error(request, 'Enrollment number already exists!')
                    return redirect('student_list')
                
                # Check if the username already exists in the User model
                # This is to ensure that the username is unique across all users
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'User already exists!')
                    return redirect('student_list')
                
                user = User.objects.create_user(username=username, password=username)
                Student.objects.create(
                    user=user,
                    enrollment=username,
                    name=name,
                    branch=branch_instance,
                    college=college_instance,
                    semester=semester,
                )

                # Add student to 'Student' group
                student_group = Group.objects.get(name='Student')
                user.groups.add(student_group)
                user.save()

                # Save the form data to the database      
                # After adding
                messages.success(request, 'Student added successfully!')
                return redirect('student_list')
            else:
                # If form is not valid, show specific errors for each field
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
        except IntegrityError as e:
            messages.error(request, f"Integrity error: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
    else:
        form = StudentsForm()

    # Filter/Search
    query = request.GET.get("search")
    if query:
        query = query.strip()
        data = data.filter(
            Q(enrollment__icontains=query) |
            Q(name__icontains=query) |
            Q(branch__name__icontains=query) |
            Q(college__name__icontains=query)
        )

    context = {
        'form': form,
        'total_count': data.count(),  # total number of records
        'data': data,
    }
    return render(request, 'adminPanel/student_list.html', context)

def delete_student_list(request, student_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    
    try:
        student = get_object_or_404(Student, id=student_id)
        user = student.user  # Get the related User instance
        # Remove student from 'Student' group
        student_group = Group.objects.get(name='Student')
        user.groups.remove(student_group)
        student.delete()  # Delete the student
        user.delete()  #  Delete the user as well
        # After deleting
        messages.success(request, 'Student deleted successfully!')

    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return redirect('student_list')
# ---------------------------- End of Student Management -----------------------

# ---------------------------- Student Subject Management -----------------------

def manage_students_subjects(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    form = StudentSubjectForm()
    branches = Department.objects.all()
    colleges = Institute.objects.all()
    subjects_list = Subject.objects.all()
    students = Student.objects.all().order_by('-id')
    subjects = Subject.objects.all().order_by('-id')
    # Fetch all student-subject relationships with related data
    data = StudentSubject.objects.select_related('student', 'subject').order_by('-id')

    if request.method == "POST":
        form = StudentSubjectForm(request.POST)
        if form.is_valid():
            enrollment = form.cleaned_data['enrollment']
            try:
                student = Student.objects.get(enrollment=enrollment)
                StudentSubject.objects.create(
                    student=student,
                    subject=form.cleaned_data['subject']
                )
                messages.success(request, 'Student Added successfully!')

                return redirect('manage_student_subjects')
            except Student.DoesNotExist:
                form.add_error('enrollment', 'Student not found.')

   
    # Filtering
    # Check if the request has a search query
    filter_field = request.GET.get("filter_field")
    search_value = request.GET.get("search_value")
    if filter_field and search_value:
        search_value = search_value.strip()
        if filter_field == "enrollment":
            data = data.filter(student__enrollment__icontains=search_value)
        elif filter_field == "name":
            data = data.filter(student__name__icontains=search_value)
        elif filter_field == "branch":
            data = data.filter(student__branch__name__icontains=search_value)
        elif filter_field == "college":
            data = data.filter(student__college__name__icontains=search_value)
        elif filter_field == "semester":
            data = data.filter(subject__semester__icontains=search_value)
        elif filter_field == "subject":
            data = data.filter(subject__subject_name__icontains=search_value)

        # 👇 Save filtered IDs in session
    request.session['filtered_student_subject_ids'] = list(data.values_list('id', flat=True))
    context = {
        'form': form,
        'students': students,
        'subjects': subjects,
        'branches': list(branches.values('name')),
        'colleges': list(colleges.values('name')),
        'subjects_list': list(subjects_list.values('subject_name')),
        'data': data,
    }
    return render(request, 'adminPanel/manage_student_subjects.html', context)


def delete_students_subjects(request, student_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    student = get_object_or_404(StudentSubject, id=student_id)
    student.delete()
    messages.success(request, 'Student deleted successfully!')
    return redirect('manage_student_subjects')
# ---------------------------- End of Student Subject Management -----------------------

# ---------------------------- Export to PDF -----------------------
class PDF(FPDF):
    def header(self):
        logo_path = os.path.join('static', 'img', 'college_logo.png')
        logo_path_b = os.path.join('static', 'img', 'bteup.jpg')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25)

        #for bteup logo  
        if os.path.exists(logo_path_b):
            self.image(logo_path_b, 175, 8, 25)
        self.set_font("Helvetica", "B", 15)

        # Long title
        title = "Mahamaya Polytechnic of Information Technology, Hariharpur, Gorakhpur (4429)"
        max_width = 120

        # Wrap and center the long title
        lines = self.wrap_text(title, max_width)
        for line in lines:
            line_width = self.get_string_width(line) + 4
            self.set_x((210 - line_width) / 2)
            self.cell(line_width, 10, line, ln=True)
        self.ln(3)
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True, align='R')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
    # ---------------------------- End of Header -----------------------
    # ---------------------------- Student Admit Card Detail Manage -----------------------
    from PIL import Image

    def student_info(self, student):
        self.set_font("Arial", "", 12)
        
        # If the student has a profile picture, add it to the PDF
        if student.profile_pic:
            # Get the absolute path of the student's profile picture
            img_path = student.profile_pic.path
            
            # Open the image
            img = Image.open(img_path).convert("RGB")
            
            # Set the fixed width and height (in mm)
            fixed_width = 40  # 40mm (fixed width)
            fixed_height = 40  # 40mm (fixed height)

            # Resize the image to fit the fixed width and height
            img = img.resize((fixed_width * 10, fixed_height * 10), Image.Resampling.LANCZOS)  # Convert mm to pixels

            # Create a BytesIO buffer to hold the resized image in memory
            from io import BytesIO
            img_byte_array = BytesIO()
            img.save(img_byte_array, format='JPEG')
            img_byte_array.seek(0)

            # Position the image (centered) with the fixed width and height
            self.image(img_byte_array, x=160, y=56, w=fixed_width, h=fixed_height)  # Set width and height to 40mm
            self.ln(3)  # Move the cursor down to leave space for the image

        # Print student details
        self.cell(0, 10, f"Enrollment Number: {student.enrollment}", ln=True)
        self.cell(0, 10, f"Name: {student.name}", ln=True)
        self.cell(0, 10, f"Branch: {student.branch}", ln=True)
        self.cell(0, 10, f"Semester: {student.semester}", ln=True)
        self.multi_cell(130, 10, f"Institute: {student.college.full_name_institute}", ln=True)

    # ---------------------------- End of Student Info -----------------------
    # ---------------------------- Student Admit Subjects Table -----------------------
    def subject_table(self, student_subjects, title="Subjects"):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", "", 12)

        # Table headers
        headers = ["Code", "Name", "Date", "Time"]
        widths = [40, 90, 30, 30]
        line_height = 6
        padding_left = 2
        default_font_size = 12
        min_font_size = 8
        fill = True  # For alternating row color

        # Header row
        for i, header in enumerate(headers):
            self.cell(widths[i], 10, header, 1, 0, 'C')
        self.ln()

        for entry in student_subjects:
            subject = entry.subject if hasattr(entry, 'subject') else entry

            # Get exam details
            exam = ExamDetail.objects.filter(subject=subject).first()
            exam_date = exam.exam_date.strftime("%d-%m-%Y") if exam else "-"
            exam_time = f"{exam.start_time.strftime('%I:%M %p')} - {exam.end_time.strftime('%I:%M %p')}" if exam else "-"

            row = [
                subject.subject_code,
                subject.subject_name,
                exam_date,
                exam_time
            ]

            wrapped_cells = []
            max_lines = 1

            for text, width in zip(row, widths):
                self.set_font("Arial", "", default_font_size)
                words = str(text).split()
                lines, current_line = [], ''

                for word in words:
                    test_line = f"{current_line} {word}" if current_line else word
                    if self.get_string_width(test_line) < (width - 2 * padding_left):
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)

                wrapped_cells.append(lines)
                max_lines = max(max_lines, len(lines))

            row_height = line_height * max_lines + 2
            x_start = self.get_x()
            y_start = self.get_y()

            for i, cell_lines in enumerate(wrapped_cells):
                x = self.get_x()
                y = self.get_y()
                width = widths[i]

                # Fill background if enabled
                if fill:
                    self.set_fill_color(245, 245, 245)
                    self.rect(x, y, width, row_height, style='F')

                # Draw border
                self.rect(x, y, width, row_height)

                # Adjust font size to fit
                font_size = default_font_size
                while any(self.get_string_width(line) > (width - 2 * padding_left) for line in cell_lines) and font_size > min_font_size:
                    font_size -= 0.5
                self.set_font("Arial", "", font_size)

                # Vertical centering
                actual_text_height = len(cell_lines) * line_height
                y_text = y + (row_height - actual_text_height) / 2

                for j, line in enumerate(cell_lines):
                    self.set_xy(x + padding_left, y_text + j * line_height)
                    self.cell(width - 2 * padding_left, line_height, line, ln=0, align='C')

                self.set_xy(x + width, y)  # Move to next column

            self.set_xy(x_start, y_start + row_height)
            fill = not fill  # Optional: alternate row color

    def signature_boxes(self):
        self.ln(10)  # Add some vertical space before the boxes

        # Set X position and draw two boxes side by side
        page_width = self.w - 2 * self.l_margin  # Total page width excluding margins
        box_width = page_width / 2 - 10  # Width of each box
        box_height = 25  # Height of signature box

        # Student Signature Box
        self.set_font("Arial", size=10)
        self.cell(box_width, box_height, "", border=1, ln=0, align='C')
        self.cell(20, box_height, "", border=0, ln=0)  # Gap between boxes

        # Principal Signature Box
        self.cell(box_width, box_height, "", border=1, ln=1, align='C')

        # Signature labels
        self.set_font("Arial", style='B', size=10)
        self.cell(box_width, 10, "Student Signature", ln=0, align='C')
        self.cell(20, 10, "", ln=0)
        self.cell(box_width, 10, "Principal Signature", ln=1, align='C')


    # ---------------------------- End of Student Admit Card Detail Manage -----------------------
    # 🔧 Move this helper inside the PDF class
    def wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.get_string_width(test_line) < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    def wrap_cell_text(self, text, width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.get_string_width(test_line) <= width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines


    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 10, "Generated by Exam Management System", align='L')
        self.cell(0, 10, f"Page {self.page_no()}", align='R')
    
# ---------------------------- Export Student Subjects to PDF -----------------------

def export_subjects_pdf(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    ids = request.session.get('filtered_student_subject_ids')

    if ids is not None:
        if ids:
            data = StudentSubject.objects.filter(id__in=ids).select_related('student', 'subject')
        else:
            data = StudentSubject.objects.none()  # empty
    else:
        data = StudentSubject.objects.select_related('student', 'subject')

    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Back Paper Details Report", ln=True, align='C')
    pdf.line(80, pdf.get_y(), 130, pdf.get_y())
    pdf.ln(2)
    # Check if data is empty
    if not data.exists():
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No records found to export.", ln=True, align='C')
    else:
        # Table headers
        header = ["S.No", "Enrollment", "Name", "Branch", "College", "Sem", "Subject"]
        # widths = [10, 50, 40, 35, 20, 30]
        widths = [10, 40, 40, 20, 25, 15, 40]
        pdf.set_fill_color(230, 230, 230)
        pdf.set_text_color(0)
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.3)
        pdf.set_font("Helvetica", "B", 11)

        for header, width in zip(header, widths):
            pdf.cell(width, 10, header, border=1, align='C', fill=True)
        pdf.ln()

        # Table body
        pdf.set_font("Helvetica", "", 10)
        fill = False
        # for idx, duty in enumerate(duties, start=1):
        line_height = 5
        padding_left = 2
        min_font_size = 6
        default_font_size = 10

        fill = False  # for striped rows
        

        for idx, item in enumerate(data, 1):
            row = [
                str(idx),
                item.student.enrollment,
                item.student.name,
                item.student.branch.name,
                item.student.college.name,
                str(item.subject.semester),
                item.subject.subject_name
            ]

            wrapped_cells = []
            max_lines = 1
            for text, width in zip(row, widths):
                pdf.set_font("Helvetica", "", default_font_size)
                lines = []
                words = str(text).split()
                current_line = ''
                for word in words:
                    test_line = current_line + ' ' + word if current_line else word
                    if pdf.get_string_width(test_line) < (width - 2 * padding_left):
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                wrapped_cells.append(lines)
                max_lines = max(max_lines, len(lines))

            row_height = line_height * max_lines + 2
            x_start = pdf.get_x()
            y_start = pdf.get_y()

            for i in range(len(row)):
                x = pdf.get_x()
                y = pdf.get_y()
                cell_lines = wrapped_cells[i]
                content = row[i]
                width = widths[i]

                # Background fill for striping
                if fill:
                    pdf.set_fill_color(245, 245, 245)
                    pdf.rect(x, y, width, row_height, style='F')  # filled background

                # Border
                pdf.rect(x, y, width, row_height)

                # Adjust font size if needed
                font_size = default_font_size
                while any(pdf.get_string_width(line) > width - 2 * padding_left for line in cell_lines) and font_size > min_font_size:
                    font_size -= 0.5
                    pdf.set_font("Helvetica", "", font_size)
                
                # Recalculate vertical centering
                actual_text_height = len(cell_lines) * line_height
                y_text = y + (row_height - actual_text_height) / 2

                # Draw each line (vertically centered)
                for j, line in enumerate(cell_lines):
                    pdf.set_xy(x + padding_left, y_text + j * line_height)
                    pdf.cell(width - 2 * padding_left, line_height, line, ln=0, align='L')

                pdf.set_xy(x + width, y)

            pdf.set_xy(x_start, y_start + row_height)
            fill = not fill  # toggle row background

        # 👇 Yahan session clear karo
    request.session.pop('filtered_student_subject_ids', None)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=student_subjects.pdf"
    pdf_bytes = bytes(pdf.output(dest='S'))  # clean output
    response.write(pdf_bytes)
    return response
# ---------------------------- End of Export to PDF -----------------------

# ------------------------------ Invigilator Duties Detail Management -----------------------

def invigilator_duties_detail(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    teacher_form = TeacherForm()
    exam_form = ExamForm()
    venue_form = VenueForm()

    if request.method == 'POST':
        try:
            if 'submit_teacher' in request.POST:
                teacher_form = TeacherForm(request.POST)
                if teacher_form.is_valid():
                    teacher_form.save()
                    messages.success(request, 'Teacher added successfully!')
                    return redirect('duty_detail')
                else:
                    messages.error(request, 'Please correct the errors in the Teacher form.')

            elif 'submit_exam' in request.POST:
                exam_form = ExamForm(request.POST)
                if exam_form.is_valid():
                    exam_form.save()
                    messages.success(request, 'Exam Schedule added successfully!')
                    return redirect('duty_detail')
                else:
                    messages.error(request, 'Please correct the errors in the Exam form.')

            elif 'submit_venue' in request.POST:
                venue_form = VenueForm(request.POST)
                if venue_form.is_valid():
                    venue_form.save()
                    messages.success(request, 'Venue added successfully!')
                    return redirect('duty_detail')
                else:
                    messages.error(request, 'Please correct the errors in the Venue form.')

        except DatabaseError as e:
            messages.error(request, f'Database error occurred: {str(e)}')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')

    teachers = Teacher.objects.all().order_by('-id')  # Fetch most recent entries
    exams = Exam.objects.all().order_by('-id')        # Fetch most recent entries
    venues = Venue.objects.all().order_by('-id')       # Fetch most recent entries

    context = {
        'teacher_form': teacher_form,
        'exam_form': exam_form,
        'venue_form': venue_form,
        'teachers': teachers,
        'exams': exams,
        'venues': venues,
    }
    return render(request, 'adminPanel/invigilator_duties_detail.html', context)

# ------------------------------ Invigilator Duties Management -----------------------


def invigilator_duties_view(request):
    if not request.session.get('admin_id'):
        return redirect('login')

    duties = InvigilatorDuty.objects.select_related('teacher', 'exam', 'venue').all().order_by('-id')
    exams = Exam.objects.all()
    teachers = list(Teacher.objects.all())
    venues = list(Venue.objects.all())

    if request.method == "POST":
        try:
            with transaction.atomic():
                venue_usage_count = defaultdict(int)
                for duty in InvigilatorDuty.objects.all():
                    venue_usage_count[duty.venue_id] += 1

                if len(teachers) < 2:
                    messages.error(request, "Not enough teachers to assign duties.")
                    return redirect('invigilator_duties')

                duties_assigned = 0  # ✅ Counter

                for exam in exams:
                    existing_teacher_ids = InvigilatorDuty.objects.filter(exam=exam).values_list('teacher_id', flat=True)
                    available_teachers = [t for t in teachers if t.id not in existing_teacher_ids]

                    if len(available_teachers) < 2:
                        messages.warning(request, f"Not enough teachers left for exam {exam.id}. Skipping...")
                        continue

                    valid_venues = [v for v in venues if venue_usage_count[v.id] < 2]
                    if len(valid_venues) < 1:
                        messages.warning(request, f"No available venues for exam {exam.id}. Skipping...")
                        continue

                    selected_teachers = random.sample(available_teachers, 2)
                    selected_venue = random.choice(valid_venues)
                    venue_usage_count[selected_venue.id] += 1

                    for teacher in selected_teachers:
                        InvigilatorDuty.objects.create(
                            teacher=teacher,
                            exam=exam,
                            venue=selected_venue,
                            status="assigned"
                        )
                        duties_assigned += 1

                if duties_assigned > 0:
                    messages.success(request, f"{duties_assigned} duties assigned successfully!")
                else:
                    messages.info(request, "No duties were assigned. Please check available data.")
                
                return redirect('invigilator_duties')

        except IntegrityError:
            messages.error(request, "Database integrity error occurred while assigning duties.")
        except ValidationError as ve:
            messages.error(request, f"Validation error: {ve}")
        except DatabaseError as de:
            messages.error(request, f"Database error: {de}")    
        except Exception as e:
            messages.error(request, f"Error during duty assignment: {str(e)}")
            return redirect('invigilator_duties')

    return render(request, 'adminPanel/invigilator_duties.html', {
        'duties': duties,
    })
# ------------------------------ Delete Invigilator Duties -----------------------


def delete_invigilator_duty(request, duty_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    duty = get_object_or_404(InvigilatorDuty, id=duty_id)
    duty.delete()
    messages.success(request, "Duty deleted successfully.")
    return redirect('invigilator_duties')  # Replace with your actual URL name
# ------------------------------ Delete All Invigilator Duties -----------------------


def delete_all_duties_view(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    if request.method == "POST":
        try:
            InvigilatorDuty.objects.all().delete()
            messages.success(request, "All invigilator duties deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting duties: {str(e)}")
        return redirect('invigilator_duties')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('invigilator_duties')
# ---------------------------- Export Invigilator Duties to PDF -----------------------

def export_duties_pdf(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    duties = InvigilatorDuty.objects.select_related('teacher', 'exam', 'venue').all()
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Invigilator Duty Details Report", ln=True, align='C')
    pdf.line(80, pdf.get_y(), 130, pdf.get_y())
    pdf.ln(2)
    headers = ["#", "Faculty", "Paper Name", "Date", "Time", "Venue", "Status"]
    widths = [10, 40, 30, 30, 35, 15, 30]

    line_height = 5
    padding_left = 2
    min_font_size = 6
    default_font_size = 10

    # Header
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(0)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.3)
    pdf.set_font("Helvetica", "B", 11)

    for header, width in zip(headers, widths):
        pdf.cell(width, 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Body
    pdf.set_font("Helvetica", "", default_font_size)
    fill = False

    for idx, duty in enumerate(duties, start=1):
        row = [
            str(idx),
            duty.teacher.name if duty.teacher else "",
            duty.exam.name if duty.exam else "",
            duty.exam.date.strftime("%d %b %Y") if duty.exam and duty.exam.date else "",
            f"{duty.exam.start_time} - {duty.exam.end_time}" if duty.exam else "",
            duty.venue.name if duty.venue else "",
            duty.status.title() if duty.status else "",
        ]

        wrapped_cells = []
        max_lines = 1

        for text, width in zip(row, widths):
            pdf.set_font("Helvetica", "", default_font_size)
            words = str(text).split()
            lines, current_line = [], ''

            for word in words:
                test_line = f"{current_line} {word}" if current_line else word
                if pdf.get_string_width(test_line) < (width - 2 * padding_left):
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            wrapped_cells.append(lines)
            max_lines = max(max_lines, len(lines))

        row_height = line_height * max_lines + 2
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i, cell_lines in enumerate(wrapped_cells):
            x = pdf.get_x()
            y = pdf.get_y()
            width = widths[i]

            # Background fill
            if fill:
                pdf.set_fill_color(245, 245, 245)
                pdf.rect(x, y, width, row_height, style='F')

            # Border
            pdf.rect(x, y, width, row_height)

            # Adjust font size if needed
            font_size = default_font_size
            while any(pdf.get_string_width(line) > (width - 2 * padding_left) for line in cell_lines) and font_size > min_font_size:
                font_size -= 0.5
            pdf.set_font("Helvetica", "", font_size)

            # Center text vertically
            actual_text_height = len(cell_lines) * line_height
            y_text = y + (row_height - actual_text_height) / 2

            for j, line in enumerate(cell_lines):
                pdf.set_xy(x + padding_left, y_text + j * line_height)
                pdf.cell(width - 2 * padding_left, line_height, line, ln=0, align='L')

            pdf.set_xy(x + width, y)

        pdf.set_xy(x_start, y_start + row_height)
        fill = not fill

    # Footer - Total duties
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, f"Total Duties Assigned: {len(duties)}", ln=True)

    # Return response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invigilator_duties.pdf"'
    response.write(bytes(pdf.output(dest='S')))
    return response

# ------------------------------ End of Invigilator Duties Management -----------------------

# ------------------------------ Delete Exam Data -----------------------

def delete_exam_duty(request, exam_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    exam = get_object_or_404(Exam, id=exam_id)
    exam.delete()
    messages.success(request, "Exam Detail deleted successfully.")
    return redirect('duty_detail')  # Replace with your actual URL name

# ------------------------------ Delete Teacher Data -----------------------

def delete_teacher_duty(request, teacher_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    messages.success(request, "Teacher data deleted successfully.")
    return redirect('duty_detail')  # Replace with your actual URL name

# ------------------------------ Delete Venue Data -----------------------

def delete_venue_duty(request, venue_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    venue = get_object_or_404(Venue, id=venue_id)
    venue.delete()
    messages.success(request, "Venue deleted successfully.")
    return redirect('duty_detail')  # Replace with your actual URL name

# ------------------------------- Admin logout function ----------------
def admin_logout(request):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    request.session.pop('admin_id', None)
    messages.success(request, "Admin logged out successfully!")
    return redirect('login')

# -------------------------- Student Update Profile Pic function -----------
@login_required(login_url='login')
@user_passes_test(is_student, login_url='login')
def update_student_profile(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)

        student.email = request.POST.get('email')
        student.mobile = request.POST.get('mobile')
        student.gender = request.POST.get('gender')
        student.father_name = request.POST.get('father_name')
        student.mother_name = request.POST.get('mother_name')
        student.father_mobile = request.POST.get('father_mobile')
        student.blood_group = request.POST.get('blood_group')
        student.semester = request.POST.get('semester')

        # Password update
        new_password = request.POST.get('password')
        if new_password:
            student.user.password = make_password(new_password)
            student.user.save()

        # Photo update
        new_profile_pic = request.FILES.get('profile_pic')

        if new_profile_pic:
            default_pic_name = 'student.png'  # adjust if your file is named differently
            old_pic_path = student.profile_pic.path if student.profile_pic else None

            if old_pic_path and os.path.basename(old_pic_path) != default_pic_name:
                if os.path.exists(old_pic_path):
                    os.remove(old_pic_path)

            student.profile_pic = new_profile_pic

        student.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ------------------------- Delete receipt request by admin -----------------
def delete_receipt(request, receipt_id):
    if not request.session.get('admin_id'):
        return redirect('login')  # Staff check
    receipt = get_object_or_404(FeeReceipt, id=receipt_id)
    student_name = receipt.student.name  # assuming ForeignKey to Student model
    receipt.delete()
    messages.success(request, f"{student_name}'s fee receipt has been deleted.")
    return redirect('admin_receipt_requests')  # redirect to your listing page



# ------------------------ Admit card exam detail manage function -----------------------
def manage_exam_details(request):
    if request.method == 'POST':
        form = ExamDetailForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_exam_details')
    else:
        form = ExamDetailForm()

    exam_details = ExamDetail.objects.select_related('subject').all()
    return render(request, 'adminPanel/manage_exam_details.html', {'form': form, 'exam_details': exam_details})

def delete_exam_detail(request, examDetail_id):
    exam = get_object_or_404(ExamDetail, id=examDetail_id)
    exam.delete()
    messages.success(request, f"Exam for subject '{exam.subject.subject_name}' has been deleted successfully.")
    return redirect('manage_exam_details')

