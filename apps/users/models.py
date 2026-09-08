"""
Users — Custom User Model
===========================
Phone-based user model with no email field.
The phone number is the sole identifier (USERNAME_FIELD).
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.common.validators import validate_egyptian_phone, validate_birthday


class UserManager(BaseUserManager):
    """Custom manager for User model using phone as the unique identifier."""

    def create_user(self, phone, password=None, **extra_fields):
        """Create and return a regular user with a phone number and password."""
        if not phone:
            raise ValueError("رقم الهاتف مطلوب.")

        phone = validate_egyptian_phone(phone)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.BUYER)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model — phone number is the primary identifier.
    No email field exists anywhere in this model.
    """

    class Role(models.TextChoices):
        BUYER = "buyer", "Buyer"

    phone = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        validators=[validate_egyptian_phone],
        verbose_name="رقم الهاتف",
        help_text="Egyptian mobile number (e.g., 01012345678)",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="الاسم",
    )
    birthday = models.DateField(
        validators=[validate_birthday],
        verbose_name="تاريخ الميلاد",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.BUYER,
        verbose_name="الدور",
    )

    # Status flags
    is_active = models.BooleanField(
        default=False,
        help_text="Activated after OTP verification.",
    )
    is_staff = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Manager
    objects = UserManager()

    # Auth config
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name", "birthday"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"
