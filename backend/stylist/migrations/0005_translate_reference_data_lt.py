from django.db import migrations


def translate_reference_data(apps, schema_editor):
    Season = apps.get_model("stylist", "Season")
    Occasion = apps.get_model("stylist", "Occasion")
    StyleTag = apps.get_model("stylist", "StyleTag")

    season_names = {
        "spring": "Pavasaris",
        "summer": "Vasara",
        "autumn": "Ruduo",
        "winter": "Žiema",
    }
    occasion_names = {
        "casual-day": "Laisvalaikis",
        "office": "Biuras",
        "date-night": "Pasimatymas",
        "formal-event": "Oficialus renginys",
        "travel": "Kelionė",
    }
    style_names = {
        "minimal": "Minimalistinis",
        "classic": "Klasikinis",
        "streetwear": "Gatvės stilius",
        "smart-casual": "Smart casual",
        "creative": "Kūrybiškas",
    }

    for code, name in season_names.items():
        Season.objects.filter(code=code).update(name=name)

    for code, name in occasion_names.items():
        Occasion.objects.filter(code=code).update(name=name)

    for code, name in style_names.items():
        StyleTag.objects.filter(code=code).update(name=name)


def reverse_translate_reference_data(apps, schema_editor):
    Season = apps.get_model("stylist", "Season")
    Occasion = apps.get_model("stylist", "Occasion")
    StyleTag = apps.get_model("stylist", "StyleTag")

    season_names = {
        "spring": "Spring",
        "summer": "Summer",
        "autumn": "Autumn",
        "winter": "Winter",
    }
    occasion_names = {
        "casual-day": "Casual day",
        "office": "Office",
        "date-night": "Date night",
        "formal-event": "Formal event",
        "travel": "Travel",
    }
    style_names = {
        "minimal": "Minimal",
        "classic": "Classic",
        "streetwear": "Streetwear",
        "smart-casual": "Smart casual",
        "creative": "Creative",
    }

    for code, name in season_names.items():
        Season.objects.filter(code=code).update(name=name)

    for code, name in occasion_names.items():
        Occasion.objects.filter(code=code).update(name=name)

    for code, name in style_names.items():
        StyleTag.objects.filter(code=code).update(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("stylist", "0004_rename_stylist_sty_status_44663f_idx_stylist_sty_status_5eb0e9_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(translate_reference_data, reverse_translate_reference_data),
    ]
