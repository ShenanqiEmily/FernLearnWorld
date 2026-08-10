from django.db import migrations


def normalize_language(apps, schema_editor):
    Vocabulary = apps.get_model("vocabulary", "Vocabulary")
    Vocabulary.objects.filter(language__iexact="japanese").update(language="japanese")
    Vocabulary.objects.filter(language__iexact="chinese").update(language="chinese")


def noop_reverse(apps, schema_editor):
    # Casing is intentionally not reversible — lowercase is the only value
    # the model's LANGUAGE_CHOICES actually defines.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("vocabulary", "0006_seed_practice_flashcard_achievements"),
    ]

    operations = [
        migrations.RunPython(normalize_language, noop_reverse),
    ]
