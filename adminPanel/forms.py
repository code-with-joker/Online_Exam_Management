from django import forms
from django.core.validators import RegexValidator
from .models import *
from django.core.exceptions import ValidationError
import re


# ----- This form is used to add a new department in the admin panel. -----
class DepartmentForm(forms.ModelForm):
    # Applying RegexValidator to ensure the 'code' field contains only digits
    code_validator = RegexValidator(regex=r'^\d+$', message="Department code must be a valid integer.")
    
    class Meta:
        model = Department
        fields = ['code', 'name', 'full_name_branch']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'e.g. 755'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. cse'}),
            'full_name_branch': forms.TextInput(attrs={'placeholder': 'e.g. Computer Science and Engineering'}),
        }

    # Assigning the RegexValidator to the 'code' field
    code = forms.CharField(validators=[code_validator])

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if Department.objects.filter(code=code).exists():
            # Reset the form field value to blank if the code exists
            self.data = self.data.copy()
            self.data['code'] = ''
            raise forms.ValidationError("Department code already exists.")
        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip().upper()

        if Department.objects.filter(name=name).exists():
            # Reset the form field value to blank if the name exists
            self.data = self.data.copy()
            self.data['name'] = ''
            raise forms.ValidationError("Department name already exists.")
        return name
    
    def clean_full_name_branch(self):
        full_name_branch = self.cleaned_data.get('full_name_branch', '').strip().upper()
        # Optional: Add additional validation for full_name_branch if necessary
        return full_name_branch

# ------- This form is used to add a new student in the admin panel. ------
# It includes a RegexValidator to ensure the enrollment number follows a specific pattern.
class StudentsForm(forms.ModelForm):
    # RegexValidator for 'enrollment' field to enforce specific pattern
    enrollment_validator = RegexValidator(
        regex=r'^E\d{14}$',  # Starts with 'E' followed by 14 digits
        message="Enrollment number must start with 'E' and be followed by 14 digits, with no special characters or spaces."
    )
    
    class Meta:
        model = Student
        fields = ['enrollment', 'name', 'branch', 'semester', 'college']
        widgets = {
            'enrollment': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.Select(attrs={'class': 'form-select'}),
        }

    # Apply the RegexValidator to the 'enrollment' field
    enrollment = forms.CharField(validators=[enrollment_validator])

    def clean_enrollment(self):
        enrollment = self.cleaned_data.get('enrollment').strip()
        return enrollment

        
# ------------- form for adding a new institute in the admin panel -------------
# It includes a RegexValidator to ensure the code is a valid integer.
class InstituteForm(forms.ModelForm):
    class Meta:
        model = Institute
        fields = ['code', 'name', 'full_name_institute']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400', 
                'placeholder': 'e.g. 4429'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 dark:text-gray-300 focus:ring-blue-400', 
                'placeholder': 'e.g. MMIT'
            }),
            'full_name_institute': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 dark:text-gray-300 focus:ring-blue-400', 
                'placeholder': 'e.g. Mahamaya Polytechnic Of Information Technology, Hariharpur, Gorakhpur'
            }),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '')
        
        if Institute.objects.filter(code=code).exists():
            # Reset the form field value to blank if the code exists
            self.data = self.data.copy()
            self.data['code'] = ''
            raise forms.ValidationError("Institute code already exists.")
        return code

    def clean_name(self):
        name = self.cleaned_data['name'].strip().upper()
        return name
    
    def clean_full_name_institute(self):
        full_name_institute = self.cleaned_data.get('full_name_institute', '').strip().upper()
        # Optional: Add additional validation for full_name_branch if necessary
        return full_name_institute
    
# ---------- form for adding a new subject in the admin panel ----------
# It includes a RegexValidator to ensure the subject code is a valid integer.
class SubjectForm(forms.ModelForm):
    subject_code = forms.CharField(
        validators=[RegexValidator(regex=r'^\d+$', message="Subject code must be an integer.")],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Subject
        ordering = ['subject_code']
        fields = ['subject_code', 'subject_name', 'semester', 'department']
        widgets = {
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_name': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

# --------- form for adding a new student-subject relationship in the admin panel -----
class StudentSubjectForm(forms.ModelForm):
    enrollment = forms.CharField(label="Enrollment Number", widget=forms.TextInput(attrs={
        'class': 'form-control', 'list': 'enrollments', 'placeholder': 'Enter or choose enrollment'
    }))

    class Meta:
        model = StudentSubject
        fields = ['enrollment', 'subject']
        widgets = {
            'semester': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Name'}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name','date', 'start_time', 'end_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Name'}),
            'date' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time' : forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time' : forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. cr 1'}),
        }   

# # --------- form for Editing Student detail ---------
class StudentEditForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Student
        fields = ['email', 'mobile', 'gender', 'father_name', 'mother_name', 'father_mobile', 'blood_group', 'semester', 'profile_pic', 'password']

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if not re.match(r'^\d{10}$', mobile):
            raise ValidationError("Enter a valid 10-digit mobile number")
        return mobile

    def clean_father_mobile(self):
        mobile = self.cleaned_data['father_mobile']
        if not re.match(r'^\d{10}$', mobile):
            raise ValidationError("Enter a valid 10-digit father's mobile number")
        return mobile

    def clean_blood_group(self):
        bg = self.cleaned_data['blood_group'].upper()
        if not re.match(r'^(A|B|AB|O)[+-]$', bg):
            raise ValidationError("Enter a valid blood group (e.g., A+, B-, AB+)")
        return bg

    def save(self, commit=True):
        instance = super().save(commit=False)

        password = self.cleaned_data.get('password')
        if password:
            from django.contrib.auth.hashers import make_password
            instance.password = make_password(password)

        if self.cleaned_data.get('profile_pic') and self.instance.profile_pic:
            self.instance.profile_pic.delete(save=False)

        if commit:
            instance.save()
        return instance



class ExamDetailForm(forms.ModelForm):
    class Meta:
        model = ExamDetail
        fields = ['subject', 'exam_date', 'start_time', 'end_time']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
        
# class LoginForm(forms.Form):
#     username = forms.CharField(label="Enrollment/Admin Username")
#     password = forms.CharField(widget=forms.PasswordInput)