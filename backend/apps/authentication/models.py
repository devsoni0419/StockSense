from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
import random

class UserRole(models.TextChoices):
    MANAGER = 'MANAGER', 'Inventory Manager'
    STAFF = 'STAFF', 'Warehouse Staff'

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STAFF
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def is_manager(self):
        return self.role == UserRole.MANAGER or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_otp_for_user(cls, user):
        otp = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        return cls.objects.create(user=user, otp_code=otp, expires_at=expires_at)

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email}: {self.otp_code}"
