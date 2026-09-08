"""
Developer Accounts — Models
=============================
DeveloperAccount (the company/org), DeveloperUser (email-based auth),
and Permission (RBAC lookup table).
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from apps.common.models import TimestampedModel


class Permission(models.Model):
    """RBAC permission lookup table, seeded via data migration."""

    codename = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["codename"]

    def __str__(self):
        return f"{self.codename} ({self.name})"


class DeveloperAccount(TimestampedModel):
    """The company/org entity that groups developers, projects, and leads."""

    company_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.company_name


class DeveloperUserManager(BaseUserManager):
    """Custom manager for DeveloperUser — email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("البريد الإلكتروني مطلوب.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user


class DeveloperUserStatus(models.TextChoices):
    ACTIVE = "active", "نشط"
    INACTIVE = "inactive", "غير نشط"


class DeveloperUser(AbstractBaseUser):
    """
    Developer/marketer user — completely separate from the buyer User model.
    Uses email+password with DRF TokenAuthentication.
    """

    account = models.ForeignKey(
        DeveloperAccount,
        on_delete=models.CASCADE,
        related_name="members",
    )
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to="developer_avatars/", null=True, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="True for the account creator, False for invited team members.",
    )
    status = models.CharField(
        max_length=10,
        choices=DeveloperUserStatus.choices,
        default=DeveloperUserStatus.ACTIVE,
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="developer_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Auth config
    objects = DeveloperUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def has_perm(self, perm, obj=None):
        """Check if user has a specific permission codename."""
        if self.is_primary:
            return True
        return self.permissions.filter(codename=perm).exists()

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return False

    @property
    def is_active(self):
        return self.status == DeveloperUserStatus.ACTIVE
