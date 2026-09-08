from django.db import migrations

def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("developer_accounts", "Permission")
    permissions_to_seed = [
        {"codename": "view_leads", "name": "عرض العملاء المحتملين"},
        {"codename": "rate_leads", "name": "تقييم العملاء المحتملين"},
        {"codename": "export_excel", "name": "تصدير الإكسيل"},
        {"codename": "manage_team", "name": "إدارة الفريق"},
        {"codename": "manage_projects", "name": "إدارة المشاريع"},
    ]
    for perm_data in permissions_to_seed:
        Permission.objects.get_or_create(**perm_data)

def reverse_seed(apps, schema_editor):
    Permission = apps.get_model("developer_accounts", "Permission")
    codenames = ["view_leads", "rate_leads", "export_excel", "manage_team", "manage_projects"]
    Permission.objects.filter(codename__in=codenames).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('developer_accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, reverse_seed),
    ]
