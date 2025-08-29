# from django.db import models
# from django.contrib.auth.hashers import make_password

# class Admin(models.Model):
#     adminName = models.CharField(max_length=100)
#     adminEmail = models.EmailField(unique=True)
#     adminRole = models.CharField(max_length=50)
#     adminPassword = models.CharField(max_length=128)

#     def save(self, *args, **kwargs):
#         # Hash the password before saving
#         # Removed password hashing here to avoid double/triple hashing
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.adminName

# class Service(models.Model):
#     name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.name

# class Provider(models.Model):
#     provider_name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     location = models.CharField(max_length=100)
#     availability = models.CharField(max_length=100)
#     service = models.ForeignKey(Service, related_name='providers', on_delete=models.CASCADE)
#     admin = models.ForeignKey('Admin', related_name='providers', on_delete=models.CASCADE)

#     def __str__(self):
#         return f"{self.provider_name} - {self.service.name}"


# from django.db import models

# class Alert(models.Model):
#     title = models.CharField(max_length=200)
#     category = models.CharField(max_length=100)
#     message = models.TextField()
#     public_date = models.DateTimeField()
#     estate = models.CharField(max_length=100)
#     role = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.title} - {self.estate} - {self.role}"


# class AlertAttachment(models.Model):
#     alert = models.ForeignKey(Alert, related_name='announcement_image', on_delete=models.CASCADE)
#     announcement_image = models.FileField(
#         upload_to='alerts/', 
#         blank=True, 
#         null=True
#     )

#     def __str__(self):
#         return f"{self.alert.title} - {self.announcement_image.name}"
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Admin(models.Model):
    adminName = models.CharField(max_length=100)
    adminEmail = models.EmailField(unique=True)
    adminRole = models.CharField(max_length=50)
    adminPassword = models.CharField(max_length=128)
    def __str__(self): return self.adminName

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name


class Availability(models.TextChoices):
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"
    BUSY = "busy", "Busy"


class Provider(models.Model):
    # Name
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)

    # Contact & profile
    phone          = models.CharField(max_length=20)
    location       = models.CharField(max_length=150)
    profile_picture = models.ImageField(
        upload_to="providers/profile_pictures/", blank=True, null=True
    )

    # Meta
    availability   = models.CharField(
        max_length=100, choices=Availability.choices, default=Availability.OFFLINE
    )
    bio            = models.TextField(blank=True)
    skill          = models.CharField(max_length=120, blank=True)

    service        = models.ForeignKey(Service, related_name='providers', on_delete=models.CASCADE)
    admin          = models.ForeignKey('Admin', related_name='providers', on_delete=models.CASCADE)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} - {self.service.name}"


class ProviderPhoto(models.Model):
    provider = models.ForeignKey(Provider, related_name="photos", on_delete=models.CASCADE)
    image    = models.ImageField(upload_to="providers/work_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.full_name} - photo #{self.id}"


class ProviderReview(models.Model):
    provider      = models.ForeignKey(Provider, related_name="reviews", on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=120)
    rating        = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    comment       = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.full_name} - {self.rating}/5 by {self.reviewer_name}"

from django.db import models

class Alert(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    message = models.TextField()
    public_date = models.DateTimeField()
    estate = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.estate} - {self.role}"


class AlertAttachment(models.Model):
    alert = models.ForeignKey(Alert, related_name='announcement_image', on_delete=models.CASCADE)
    announcement_image = models.FileField(
        upload_to='alerts/', 
        blank=True, 
        null=True
    )

    def __str__(self):
        return f"{self.alert.title} - {self.announcement_image.name}"
