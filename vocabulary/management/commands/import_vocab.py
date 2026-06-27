import csv

from django.core.management.base import BaseCommand

from course.models import Course
from vocabulary.models import Vocabulary


class Command(BaseCommand):
    help = "Import vocabulary from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str)

    def handle(self, *args, **kwargs):

        csv_file = kwargs["csv_file"]

        with open(csv_file, newline="", encoding="utf-8-sig") as file:

            reader = csv.DictReader(file)

            count = 0

            for row in reader:

                course_key = row.get("course", "").strip()

                course = (
                    Course.objects.filter(code__iexact=course_key).first()
                    or Course.objects.filter(title__iexact=course_key).first()
                    or Course.objects.filter(title__icontains=course_key).first()
                    or Course.objects.filter(code__icontains=course_key).first()
                )

                if not course:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Course not found: {course_key}"
                        )
                    )
                    continue

                Vocabulary.objects.create(
                    course=course,

                    word=row.get("word", ""),
                    reading=row.get("reading", ""),
                    pinyin=row.get("pinyin", ""),

                    meaning_th=row.get("meaning_th", ""),
                    meaning_en=row.get("meaning_en", ""),

                    language=row.get("language", ""),
                    level=row.get("level", ""),

                    example_sentence=row.get("example_sentence", ""),
                    example_reading=row.get("example_reading", ""),

                    example_translation_th=row.get(
                        "example_translation_th", ""
                    ),

                    example_translation_en=row.get(
                        "example_translation_en", ""
                    ),
                )

                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {count} vocabularies"
            )
        )