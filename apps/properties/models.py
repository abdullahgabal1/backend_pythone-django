"""
Properties — Models
====================
Read-only property catalog models matching frontend contract.
"""
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from apps.common.models import TimestampedModel


class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "شقة"
    VILLA = "villa", "فيلا"
    TOWNHOUSE = "townhouse", "تاون هاوس"
    PENTHOUSE = "penthouse", "بنتهاوس"
    CHALET = "chalet", "شاليه"
    DUPLEX = "duplex", "دوبلكس"
    OFFICE = "office", "مكتب"


class CompletionStatus(models.TextChoices):
    READY = "ready", "جاهز للتسليم"
    OFF_PLAN = "off_plan", "تحت الإنشاء"


class Furnishing(models.TextChoices):
    FURNISHED = "furnished", "مفروش"
    SEMI_FURNISHED = "semi_furnished", "نصف مفروش"
    UNFURNISHED = "unfurnished", "غير مفروش"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "نقداً"
    INSTALLMENT = "installment", "تقسيط"
    MORTGAGE = "mortgage", "رهن عقاري"


class Agent(TimestampedModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    image = models.URLField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "amenities"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Property(TimestampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_suffix = models.CharField(max_length=50, blank=True, default="")
    area_sqm = models.PositiveIntegerField()
    beds = models.PositiveSmallIntegerField(help_text="0 means studio")
    baths = models.PositiveSmallIntegerField()
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
    )
    completion_status = models.CharField(
        max_length=20,
        choices=CompletionStatus.choices,
    )
    furnishing = models.CharField(
        max_length=20,
        choices=Furnishing.choices,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    parking = models.PositiveSmallIntegerField(default=0)
    # ARCHITECTURE DECISION: Property <-> Project Linkage
    # These two catalogs (Property vs Project) are intentionally loosely coupled.
    # A Property can exist independently (e.g. secondary market/resale) and uses a free-text
    # 'location' field. We DO NOT strictly migrate Property.location to locations.Location
    # because off-plan properties are bound to a Project (and its location.Location),
    # whereas secondary listings may just have free-text locations. Do not try to "fix"
    # or strictly couple these without a major product decision.
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="properties",
        help_text="Optional link to developer project. Catalogs remain loosely coupled by design.",
    )
    agent = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="properties",
    )
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name="properties",
    )
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "properties"
        indexes = [
            models.Index(fields=["completion_status"]),
            models.Index(fields=["price"]),
            models.Index(fields=["area_sqm"]),
            models.Index(fields=["property_type"]),
            models.Index(fields=["location"]),
            # Postgres trigram index for icontains queries on free-text location.
            # Requires CREATE EXTENSION pg_trgm; in the database.
            # Harmlessly ignored on SQLite.
            GinIndex(
                name="property_location_trgm",
                fields=["location"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.location}"


class PropertyImage(TimestampedModel):
    property = models.ForeignKey(
        Property,
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.URLField()
    order = models.PositiveSmallIntegerField(default=0)
    is_cover = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image {self.order} for {self.property.title}"
