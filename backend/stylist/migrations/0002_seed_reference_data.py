from django.db import migrations


def seed_reference_data(apps, schema_editor):
    Season = apps.get_model("stylist", "Season")
    Occasion = apps.get_model("stylist", "Occasion")
    StyleTag = apps.get_model("stylist", "StyleTag")

    seasons = [
        {"name": "Spring", "code": "spring", "sort_order": 10},
        {"name": "Summer", "code": "summer", "sort_order": 20},
        {"name": "Autumn", "code": "autumn", "sort_order": 30},
        {"name": "Winter", "code": "winter", "sort_order": 40},
    ]
    occasions = [
        {"name": "Casual day", "code": "casual-day", "sort_order": 10},
        {"name": "Office", "code": "office", "sort_order": 20},
        {"name": "Date night", "code": "date-night", "sort_order": 30},
        {"name": "Formal event", "code": "formal-event", "sort_order": 40},
        {"name": "Travel", "code": "travel", "sort_order": 50},
    ]
    styles = [
        {"name": "Minimal", "code": "minimal", "sort_order": 10},
        {"name": "Classic", "code": "classic", "sort_order": 20},
        {"name": "Streetwear", "code": "streetwear", "sort_order": 30},
        {"name": "Smart casual", "code": "smart-casual", "sort_order": 40},
        {"name": "Creative", "code": "creative", "sort_order": 50},
    ]

    for payload in seasons:
        Season.objects.update_or_create(code=payload["code"], defaults={**payload, "is_active": True})
    for payload in occasions:
        Occasion.objects.update_or_create(code=payload["code"], defaults={**payload, "is_active": True})
    for payload in styles:
        StyleTag.objects.update_or_create(code=payload["code"], defaults={**payload, "is_active": True})


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("stylist", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, noop_reverse),
    ]
