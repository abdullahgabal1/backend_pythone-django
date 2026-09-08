"""Seed a repeatable Egyptian property catalog for development and CI."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.properties.models import Agent, Amenity, Property


PROPERTIES = [
    ("شقة عائلية في التجمع الخامس", "التجمع الخامس", "apartment", 3, 180, 4200000, "ready", "installment"),
    ("فيلا مستقلة في الشيخ زايد", "الشيخ زايد", "villa", 5, 420, 14500000, "ready", "cash"),
    ("تاون هاوس في مدينة المستقبل", "مدينة المستقبل", "townhouse", 4, 260, 7800000, "off_plan", "installment"),
    ("شاليه بإطلالة بحرية في الساحل", "الساحل الشمالي", "chalet", 2, 125, 6200000, "ready", "cash"),
    ("دوبلكس في العاصمة الإدارية", "العاصمة الإدارية", "duplex", 3, 230, 5600000, "off_plan", "installment"),
    ("بنتهاوس في المعادي", "المعادي", "penthouse", 3, 210, 6800000, "ready", "mortgage"),
    ("مكتب إداري في القاهرة الجديدة", "التجمع الخامس", "office", 0, 95, 2500000, "off_plan", "installment"),
    ("استوديو مفروش في الغردقة", "الغردقة", "apartment", 0, 58, 1350000, "ready", "cash"),
]


class Command(BaseCommand):
    help = "Seed realistic Egyptian property data across search dimensions."

    @transaction.atomic
    def handle(self, *args, **options):
        agent, _ = Agent.objects.get_or_create(
            phone="01012345678",
            defaults={"name": "أحمد محمود", "image": "https://example.com/ahmed.jpg"},
        )
        amenities = [
            Amenity.objects.get_or_create(name=name)[0]
            for name in ("حمام سباحة", "أمن وحراسة", "مواقف سيارات", "حدائق")
        ]
        created = 0
        for title, location, property_type, beds, area, price, completion, payment in PROPERTIES:
            property_obj, was_created = Property.objects.get_or_create(
                title=title,
                defaults={
                    "description": f"وحدة مميزة في {location} بمواصفات مناسبة للسوق المصري.",
                    "location": location,
                    "price": Decimal(price),
                    "area_sqm": area,
                    "beds": beds,
                    "baths": max(1, min(4, beds)),
                    "property_type": property_type,
                    "completion_status": completion,
                    "furnishing": "unfurnished",
                    "payment_method": payment,
                    "parking": 1,
                    "agent": agent,
                    "is_featured": created % 2 == 0,
                },
            )
            if was_created:
                property_obj.amenities.set(amenities[: 2 + (created % 3)])
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} Egyptian properties."))