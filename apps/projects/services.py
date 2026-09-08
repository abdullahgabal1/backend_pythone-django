"""
Projects — Services
=====================
Business logic for creating and updating projects, including multipart file handling.
"""
from django.db import transaction
from apps.developer_accounts.models import DeveloperAccount
from apps.projects.models import Project, ProjectImage

@transaction.atomic
def create_project(account: DeveloperAccount, data: dict, files: dict) -> Project:
    project = Project.objects.create(
        account=account,
        name=data["name"],
        project_type=data["project_type"],
        location_id=data["location_id"],
        price_per_meter=data["price_per_meter"],
        description=data.get("description", ""),
        status=data.get("status", "active"),
        main_image=files["main_image"],
    )
    if "document" in files:
        project.document = files["document"]
        project.save(update_fields=["document"])

    # Handle gallery images (multiple files)
    gallery_files = files.getlist("gallery") if hasattr(files, "getlist") else []
    for idx, img in enumerate(gallery_files):
        ProjectImage.objects.create(project=project, image=img, order=idx)

    return project

@transaction.atomic
def update_project(project: Project, data: dict, files: dict) -> Project:
    if "name" in data:
        project.name = data["name"]
    if "project_type" in data:
        project.project_type = data["project_type"]
    if "location_id" in data:
        project.location_id = data["location_id"]
    if "price_per_meter" in data:
        project.price_per_meter = data["price_per_meter"]
    if "description" in data:
        project.description = data["description"]
    if "status" in data:
        project.status = data["status"]
    
    if "main_image" in files:
        project.main_image = files["main_image"]
    if "document" in files:
        project.document = files["document"]
    
    project.save()

    # Optional: If new gallery files are provided, append them.
    # To fully replace, the frontend would need to send IDs of kept images, 
    # but appending is standard for simple multipart updates.
    gallery_files = files.getlist("gallery") if hasattr(files, "getlist") else []
    start_idx = project.gallery.count()
    for idx, img in enumerate(gallery_files, start=start_idx):
        ProjectImage.objects.create(project=project, image=img, order=idx)

    return project

def delete_project(project: Project) -> None:
    project.delete()
