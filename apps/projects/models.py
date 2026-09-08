"""
Projects — Models
===================
Developer-managed compounds/developments.
"""
from django.db import models
from apps.common.models import TimestampedModel
from apps.developer_accounts.models import DeveloperAccount
from apps.locations.models import Location


class ProjectType(models.TextChoices):
    RESIDENTIAL = "residential", "سكني"
    COMMERCIAL = "commercial", "تجاري"
    MEDICAL = "medical", "طبي"


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "نشط"
    INACTIVE = "inactive", "غير نشط"


class Project(TimestampedModel):
    account = models.ForeignKey(
        DeveloperAccount,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    project_type = models.CharField(
        max_length=20,
        choices=ProjectType.choices,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    price_per_meter = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
    )
    main_image = models.ImageField(upload_to="project_images/")
    document = models.FileField(upload_to="project_documents/", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.account.company_name})"


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="gallery",
    )
    image = models.ImageField(upload_to="project_gallery/")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Gallery image {self.order} for {self.project.name}"
