from django.core.management.base import BaseCommand
from django.utils.text import slugify
from course.models import Program, Course


class Command(BaseCommand):
    help = "Create JLPT N5 lessons 11-25"

    def handle(self, *args, **options):
        program = Program.objects.get(title="JLPT N5 Japanese Course")

        lessons = [
            ("011", "Shopping & Prices", "เรียนคำศัพท์เกี่ยวกับการซื้อของ ราคา เงิน และการถามราคา"),
            ("012", "Restaurant & Food", "เรียนคำศัพท์เกี่ยวกับอาหาร เครื่องดื่ม และการสั่งอาหาร"),
            ("013", "Transportation", "เรียนคำศัพท์เกี่ยวกับรถไฟ รถบัส สถานี และการเดินทาง"),
            ("014", "Asking for Help", "เรียนประโยคขอความช่วยเหลือและการสอบถามข้อมูล"),
            ("015", "Daily Activities", "เรียนกิจวัตรประจำวันและคำกริยาพื้นฐาน"),
            ("016", "Particles は・が・を", "เรียนการใช้ は が และ を ในประโยค"),
            ("017", "Particles に・で・へ", "เรียนการใช้ に で และ へ"),
            ("018", "Present & Past Tense", "เรียนรูปปัจจุบันและอดีตของภาษาญี่ปุ่น"),
            ("019", "Negative Form", "เรียนรูปปฏิเสธของคำกริยาและประโยค"),
            ("020", "Question Form", "เรียนการสร้างประโยคคำถามด้วย か"),
            ("021", "Self Introduction", "ฝึกแนะนำตัวเองเป็นภาษาญี่ปุ่น"),
            ("022", "Talking About Family", "เรียนคำศัพท์และประโยคเกี่ยวกับครอบครัว"),
            ("023", "Talking About Hobbies", "เรียนการพูดถึงงานอดิเรกและความสนใจ"),
            ("024", "Talking About Future Plans", "เรียนการพูดถึงแผนในอนาคตและสิ่งที่อยากทำ"),
            ("025", "Final Review & Mock Test", "ทบทวนบทเรียนทั้งหมดและทำแบบทดสอบ N5"),
        ]

        for num, name, summary in lessons:
            code = f"JP-N5-{num}"
            title = f"N5 Lesson {int(num)}: {name}"
            slug = slugify(title)

            course, created = Course.objects.update_or_create(
                code=code,
                defaults={
                    "slug": slug,
                    "title": title,
                    "summary": summary,
                    "program": program,
                    "level": "N5",
                    "year": 1,
                    "semester": "First",
                    "credit": 1,
                    "is_elective": False,
                },
            )

            if hasattr(course, "title_th"):
                course.title_th = title

            if hasattr(course, "summary_th"):
                course.summary_th = summary

            course.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {code}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated {code}"))

        self.stdout.write(self.style.SUCCESS("Done: JP-N5-011 to JP-N5-025"))