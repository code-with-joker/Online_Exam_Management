from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


# ------ This model is used to create a department in the admin panel. -----
class Department(models.Model):
    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, unique=True)
    full_name_branch = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip().upper()  # Convert to ALL CAPS before saving

    # Only convert to uppercase if full_name_branch is not None
        if self.full_name_branch:
            self.full_name_branch = self.full_name_branch.strip().upper()  # Convert full name to uppercase if it exists
        
        super(Department, self).save(*args, **kwargs)    

    def __str__(self):
        return f"{self.name} ({self.code})"

# ------ This model is used to create an institute in the admin panel. -----
class Institute(models.Model):
    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    full_name_institute = models.CharField(max_length=100,null=True, blank=True)

    def save(self, *args, **kwargs):
        # self.code = self.code.upper()
        self.name = self.name.upper()
        if self.full_name_institute:
            self.full_name_institute = self.full_name_institute.upper()  # Convert full name to uppercase if it exists
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"
    
# ------ This model is used to create a subject in the admin panel. -----
# It includes a foreign key to the Department model.
class Subject(models.Model):
    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=100)
    semester = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.subject_code = self.subject_code.strip().upper()
        self.semester = self.semester.strip()
        self.subject_name = self.subject_name.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"    
    
# ------ This model is used to create a student in the admin panel. -----
# It includes a foreign key to the Department and Institute models.
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_student')
    enrollment = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.IntegerField()
    college = models.ForeignKey(Institute, on_delete=models.CASCADE)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    gender = models.CharField(max_length=10)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    father_mobile = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=5)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='student.png')

    def save(self, *args, **kwargs):
        self.enrollment = self.enrollment.strip().upper()
        self.name = self.name.strip().upper()
        
        super().save(*args, **kwargs)

    def __str__(self):

        return self.name  

# ------ This model is used to create a student-subject relationship in the admin panel. -----
class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.enrollment} - {self.subject.subject_name}"
    

class Teacher(models.Model):
    name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Store name in uppercase
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Exam(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()


    def save(self, *args, **kwargs):
        self.name = self.name.strip().upper()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Venue(models.Model):
    name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.name = self.name.upper()  # Store name in uppercase
        super().save(*args, **kwargs)
    

    def __str__(self):
        return self.name
    

class InvigilatorDuty(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ("assigned", "Assigned"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ], default="assigned")

    

    class Meta:
        unique_together = ('teacher', 'exam')  # Prevent double allocation

    def __str__(self):
        return self.teacher.name + " - " + self.exam.name + " - " + self.venue.name
    
class ExamDetail(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

