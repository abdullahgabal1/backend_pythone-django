"""
Data Seeder -- Management Command
==================================
Seed the database with Egyptian-specific demo data for development/staging.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed database with Egyptian-specific demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_locations()
        self._seed_agents()
        self._seed_amenities()
        self._seed_properties()
        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))

    def _seed_locations(self):
        from apps.locations.models import Location

        governorates = {
            "القاهرة": ["التجمع الخامس", "مدينة نصر", "المعادي", "الشروق", "العاصمة الإدارية"],
            "الجيزة": ["6 أكتوبر", "الشيخ زايد", "الهرم", "فيصل"],
            "الإسكندرية": ["سموحة", "سيدي جابر", "ستانلي", "المنتزه"],
            "البحر الأحمر": ["الغردقة", "مرسى علم", "سفاجا"],
            "جنوب سيناء": ["شرم الشيخ", "دهب", "طابا"],
            "الساحل الشمالي": ["مراسي", "هاسيندا", "العلمين الجديدة"],
        }

        created = 0
        for gov_name, areas in governorates.items():
            gov, _ = Location.objects.get_or_create(name=gov_name, parent=None)
            for area_name in areas:
                _, was_created = Location.objects.get_or_create(name=area_name, parent=gov)
                if was_created:
                    created += 1

        self.stdout.write(f"  Locations: {created} areas created.")

    def _seed_agents(self):
        from apps.properties.models import Agent

        agents = [
            {"name": "أحمد محمود", "phone": "01012345678", "image": "https://i.pravatar.cc/150?u=ahmed"},
            {"name": "سارة حسن", "phone": "01123456789", "image": "https://i.pravatar.cc/150?u=sara"},
            {"name": "محمد عبد الله", "phone": "01234567890", "image": "https://i.pravatar.cc/150?u=mohamed"},
        ]
        created = 0
        for a in agents:
            _, was_created = Agent.objects.get_or_create(phone=a["phone"], defaults=a)
            if was_created:
                created += 1
        self.stdout.write(f"  Agents: {created} created.")

    def _seed_amenities(self):
        from apps.properties.models import Amenity

        amenity_names = [
            "حمام سباحة", "نادي رياضي", "أمن 24 ساعة", "مواقف سيارات",
            "حدائق", "منطقة أطفال", "تكييف مركزي", "بلكونة",
            "مصعد", "غرفة خادمة", "تراس", "فيو مفتوح",
        ]
        created = 0
        for name in amenity_names:
            _, was_created = Amenity.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(f"  Amenities: {created} created.")

    def _seed_properties(self):
        import random
        from decimal import Decimal
        from apps.properties.models import Agent, Amenity, Property, PropertyImage

        agents = list(Agent.objects.all())
        amenities = list(Amenity.objects.all())
        if not agents:
            self.stdout.write("  No agents found, skipping properties.")
            return

        property_templates = [
            {"title": "شقة فاخرة في التجمع الخامس", "location": "التجمع الخامس", "type": "apartment", "beds": 3, "baths": 2, "area": 180, "price": 3500000},
            {"title": "فيلا مستقلة في الشيخ زايد", "location": "الشيخ زايد", "type": "villa", "beds": 5, "baths": 4, "area": 350, "price": 12000000},
            {"title": "دوبلكس بحديقة في 6 أكتوبر", "location": "6 أكتوبر", "type": "duplex", "beds": 4, "baths": 3, "area": 280, "price": 6500000},
            {"title": "شاليه على البحر في الساحل", "location": "هاسيندا", "type": "chalet", "beds": 2, "baths": 1, "area": 100, "price": 4000000},
            {"title": "بنتهاوس في العاصمة الإدارية", "location": "العاصمة الإدارية", "type": "penthouse", "beds": 3, "baths": 3, "area": 220, "price": 5500000},
            {"title": "تاون هاوس في مدينة نصر", "location": "مدينة نصر", "type": "townhouse", "beds": 4, "baths": 3, "area": 250, "price": 7000000},
            {"title": "مكتب إداري في التجمع الخامس", "location": "التجمع الخامس", "type": "office", "beds": 0, "baths": 1, "area": 80, "price": 2000000},
            {"title": "شقة استوديو في المعادي", "location": "المعادي", "type": "apartment", "beds": 0, "baths": 1, "area": 55, "price": 1200000},
            {"title": "فيلا توين هاوس في الشروق", "location": "الشروق", "type": "villa", "beds": 4, "baths": 3, "area": 300, "price": 8000000},
            {"title": "شقة فندقية في شرم الشيخ", "location": "شرم الشيخ", "type": "apartment", "beds": 1, "baths": 1, "area": 70, "price": 1800000},
        ]

        created = 0
        completions = ["ready", "off_plan"]
        furnishings = ["furnished", "semi_furnished", "unfurnished"]
        payments = ["cash", "installment", "mortgage"]

        for tmpl in property_templates:
            if Property.objects.filter(title=tmpl["title"]).exists():
                continue

            prop = Property.objects.create(
                title=tmpl["title"],
                description=f"وحدة مميزة في {tmpl['location']} بمساحة {tmpl['area']} متر مربع.",
                location=tmpl["location"],
                price=Decimal(str(tmpl["price"])),
                area_sqm=tmpl["area"],
                beds=tmpl["beds"],
                baths=tmpl["baths"],
                property_type=tmpl["type"],
                completion_status=random.choice(completions),
                furnishing=random.choice(furnishings),
                payment_method=random.choice(payments),
                parking=random.randint(0, 2),
                agent=random.choice(agents),
                is_featured=random.choice([True, False]),
            )
            prop.amenities.set(random.sample(amenities, min(5, len(amenities))))

            for i in range(3):
                PropertyImage.objects.create(
                    property=prop,
                    image=f"https://picsum.photos/seed/{prop.id}_{i}/800/600",
                    order=i,
                    is_cover=(i == 0),
                )
            created += 1

        self.stdout.write(f"  Properties: {created} created with images.")
