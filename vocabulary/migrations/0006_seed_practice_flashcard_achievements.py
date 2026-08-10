from django.db import migrations

NEW_ACHIEVEMENTS = [
    {
        "code": "PRACTICE_FIRST",
        "title": "Practice Starter",
        "icon": "🎯",
        "description": "ผ่านโหมดฝึกใน Practice Hub เป็นครั้งแรก",
    },
    {
        "code": "PRACTICE_XP_500",
        "title": "XP Hunter",
        "icon": "⚡",
        "description": "สะสม XP จาก Practice Hub ครบ 500",
    },
    {
        "code": "PRACTICE_XP_1000",
        "title": "XP Master",
        "icon": "🌟",
        "description": "สะสม XP จาก Practice Hub ครบ 1000",
    },
    {
        "code": "FLASHCARD_100",
        "title": "Flashcard Explorer",
        "icon": "🗂️",
        "description": "ทบทวนการ์ด Flashcard ครบ 100 ใบ",
    },
    {
        "code": "FLASHCARD_STREAK_7",
        "title": "7-Day Streak",
        "icon": "🔥",
        "description": "ทบทวน Flashcard ติดต่อกันครบ 7 วัน",
    },
]


def add_achievements(apps, schema_editor):
    Achievement = apps.get_model("vocabulary", "Achievement")
    for entry in NEW_ACHIEVEMENTS:
        Achievement.objects.get_or_create(
            code=entry["code"],
            defaults={
                "title": entry["title"],
                "icon": entry["icon"],
                "description": entry["description"],
            },
        )


def remove_achievements(apps, schema_editor):
    Achievement = apps.get_model("vocabulary", "Achievement")
    codes = [entry["code"] for entry in NEW_ACHIEVEMENTS]
    Achievement.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vocabulary", "0005_vocabulary_speech_aliases"),
    ]

    operations = [
        migrations.RunPython(add_achievements, remove_achievements),
    ]
