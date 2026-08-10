from django.core.management.base import BaseCommand

from flashcards.models import GrammarPoint, KanjiCharacter

GRAMMAR_POINTS = [
    dict(term="は", title="助詞 は - Topic marker", topic="particles",
         explanation_th="は (อ่านว่า wa เมื่อเป็นคำช่วย) ใช้บอกหัวข้อหลักของประโยค",
         example_sentence="私は学生です。", example_reading="わたしは がくせい です。",
         example_translation_th="ฉันเป็นนักเรียน"),
    dict(term="が", title="助詞 が - Subject marker", topic="particles",
         explanation_th="が ใช้บอกประธานของประโยค โดยเฉพาะเมื่อเน้นว่าใครเป็นผู้ทำ",
         example_sentence="猫がいます。", example_reading="ねこが います。",
         example_translation_th="มีแมวอยู่"),
    dict(term="を", title="助詞 を - Object marker", topic="particles",
         explanation_th="を ใช้บอกกรรมตรงของกริยา",
         example_sentence="パンを食べます。", example_reading="パンを たべます。",
         example_translation_th="กินขนมปัง"),
    dict(term="に", title="助詞 に - Time / direction marker", topic="particles",
         explanation_th="に ใช้บอกเวลา หรือจุดหมายปลายทาง",
         example_sentence="七時に起きます。", example_reading="しちじに おきます。",
         example_translation_th="ตื่นนอนตอนเจ็ดโมง"),
    dict(term="で", title="助詞 で - Location of action / means", topic="particles",
         explanation_th="で ใช้บอกสถานที่ที่ทำกิจกรรม หรือวิธีการ/เครื่องมือ",
         example_sentence="図書館で勉強します。", example_reading="としょかんで べんきょう します。",
         example_translation_th="เรียนหนังสือที่ห้องสมุด"),
    dict(term="へ", title="助詞 へ - Direction marker", topic="particles",
         explanation_th="へ (อ่านว่า e เมื่อเป็นคำช่วย) ใช้บอกทิศทางที่มุ่งไป",
         example_sentence="学校へ行きます。", example_reading="がっこうへ いきます。",
         example_translation_th="ไปโรงเรียน"),
    dict(term="と", title="助詞 と - And / with", topic="particles",
         explanation_th="と ใช้เชื่อมคำนามแบบ 'และ' หรือบอกว่าทำร่วมกับใคร",
         example_sentence="友達と映画を見ます。", example_reading="ともだちと えいがを みます。",
         example_translation_th="ดูหนังกับเพื่อน"),
    dict(term="も", title="助詞 も - Also / too", topic="particles",
         explanation_th="も ใช้แทนที่ は เมื่อต้องการพูดว่า 'ก็เช่นกัน'",
         example_sentence="私も学生です。", example_reading="わたしも がくせい です。",
         example_translation_th="ฉันก็เป็นนักเรียนเหมือนกัน"),
    dict(term="から", title="助詞 から - From / since", topic="particles",
         explanation_th="から ใช้บอกจุดเริ่มต้นของเวลาหรือสถานที่",
         example_sentence="九時から働きます。", example_reading="くじから はたらきます。",
         example_translation_th="ทำงานตั้งแต่เก้าโมง"),
    dict(term="まで", title="助詞 まで - Until / to", topic="particles",
         explanation_th="まで ใช้บอกจุดสิ้นสุดของเวลาหรือสถานที่",
         example_sentence="五時まで働きます。", example_reading="ごじまで はたらきます。",
         example_translation_th="ทำงานจนถึงห้าโมง"),
    dict(term="の", title="助詞 の - Possessive marker", topic="particles",
         explanation_th="の ใช้เชื่อมคำนามสองคำ คล้าย 'ของ' ในภาษาไทย",
         example_sentence="これは私の本です。", example_reading="これは わたしの ほん です。",
         example_translation_th="นี่คือหนังสือของฉัน"),
    dict(term="か", title="助詞 か - Question marker", topic="particles",
         explanation_th="か วางท้ายประโยคเพื่อทำให้เป็นประโยคคำถาม",
         example_sentence="これは何ですか。", example_reading="これは なんですか。",
         example_translation_th="นี่คืออะไร"),
    dict(term="〜ます", title="ます形 - Present polite form", topic="verb_conjugation",
         explanation_th="รูป ます ใช้พูดกริยาแบบสุภาพในประโยคปัจจุบัน/อนาคต",
         example_sentence="毎日勉強します。", example_reading="まいにち べんきょう します。",
         example_translation_th="เรียนหนังสือทุกวัน"),
    dict(term="〜ました", title="ました形 - Past polite form", topic="verb_conjugation",
         explanation_th="รูป ました ใช้พูดกริยาแบบสุภาพในประโยคอดีต",
         example_sentence="昨日勉強しました。", example_reading="きのう べんきょう しました。",
         example_translation_th="เมื่อวานเรียนหนังสือแล้ว"),
    dict(term="〜て形", title="て形 - Te-form", topic="verb_conjugation",
         explanation_th="รูป て ใช้เชื่อมประโยค ขอร้อง หรือบอกการกระทำต่อเนื่อง",
         example_sentence="ここに座ってください。", example_reading="ここに すわって ください。",
         example_translation_th="กรุณานั่งตรงนี้"),
    dict(term="〜くない", title="い-adjective negation", topic="adjectives",
         explanation_th="คำคุณศัพท์กลุ่ม い ปฏิเสธโดยเปลี่ยน い ท้ายคำเป็น くない",
         example_sentence="この本は高くないです。", example_reading="このほんは たかくない です。",
         example_translation_th="หนังสือเล่มนี้ไม่แพง"),
    dict(term="〜な", title="な-adjective connector", topic="adjectives",
         explanation_th="คำคุณศัพท์กลุ่ม な ต้องเติม な ก่อนคำนามที่ตามมา",
         example_sentence="ここは静かな公園です。", example_reading="ここは しずかな こうえん です。",
         example_translation_th="ที่นี่เป็นสวนสาธารณะที่เงียบสงบ"),
    dict(term="〜たいです", title="Want to do ~", topic="sentence_patterns",
         explanation_th="เติม たいです หลังก้านกริยารูป ます เพื่อบอกว่า 'อยากทำ'",
         example_sentence="日本へ行きたいです。", example_reading="にほんへ いきたい です。",
         example_translation_th="อยากไปญี่ปุ่น"),
    dict(term="〜てください", title="Please do ~", topic="sentence_patterns",
         explanation_th="เติม てください หลังรูป て เพื่อขอร้องให้ผู้อื่นทำสิ่งใดสิ่งหนึ่ง",
         example_sentence="ちょっと待ってください。", example_reading="ちょっと まって ください。",
         example_translation_th="กรุณารอสักครู่"),
]

KANJI_CHARACTERS = [
    dict(character="一", meaning_th="หนึ่ง", onyomi="いち", kunyomi="ひと(つ)",
         example_word="一つ", example_reading="ひとつ"),
    dict(character="二", meaning_th="สอง", onyomi="に", kunyomi="ふた(つ)",
         example_word="二つ", example_reading="ふたつ"),
    dict(character="三", meaning_th="สาม", onyomi="さん", kunyomi="みっ(つ)",
         example_word="三つ", example_reading="みっつ"),
    dict(character="四", meaning_th="สี่", onyomi="し", kunyomi="よん・よ",
         example_word="四つ", example_reading="よっつ"),
    dict(character="五", meaning_th="ห้า", onyomi="ご", kunyomi="いつ(つ)",
         example_word="五つ", example_reading="いつつ"),
    dict(character="六", meaning_th="หก", onyomi="ろく", kunyomi="むっ(つ)",
         example_word="六つ", example_reading="むっつ"),
    dict(character="七", meaning_th="เจ็ด", onyomi="しち", kunyomi="なな(つ)",
         example_word="七つ", example_reading="ななつ"),
    dict(character="八", meaning_th="แปด", onyomi="はち", kunyomi="やっ(つ)",
         example_word="八つ", example_reading="やっつ"),
    dict(character="九", meaning_th="เก้า", onyomi="きゅう・く", kunyomi="ここの(つ)",
         example_word="九つ", example_reading="ここのつ"),
    dict(character="十", meaning_th="สิบ", onyomi="じゅう", kunyomi="とお",
         example_word="十", example_reading="とお"),
    dict(character="日", meaning_th="วัน / พระอาทิตย์", onyomi="にち・じつ", kunyomi="ひ・か",
         example_word="日曜日", example_reading="にちようび"),
    dict(character="月", meaning_th="เดือน / พระจันทร์", onyomi="げつ・がつ", kunyomi="つき",
         example_word="月曜日", example_reading="げつようび"),
    dict(character="火", meaning_th="ไฟ", onyomi="か", kunyomi="ひ",
         example_word="火曜日", example_reading="かようび"),
    dict(character="水", meaning_th="น้ำ", onyomi="すい", kunyomi="みず",
         example_word="水曜日", example_reading="すいようび"),
    dict(character="木", meaning_th="ต้นไม้ / ไม้", onyomi="もく・ぼく", kunyomi="き",
         example_word="木曜日", example_reading="もくようび"),
    dict(character="金", meaning_th="ทอง / เงิน", onyomi="きん", kunyomi="かね",
         example_word="金曜日", example_reading="きんようび"),
    dict(character="土", meaning_th="ดิน", onyomi="ど・と", kunyomi="つち",
         example_word="土曜日", example_reading="どようび"),
    dict(character="人", meaning_th="คน", onyomi="じん・にん", kunyomi="ひと",
         example_word="日本人", example_reading="にほんじん"),
    dict(character="大", meaning_th="ใหญ่", onyomi="だい・たい", kunyomi="おお(きい)",
         example_word="大きい", example_reading="おおきい"),
    dict(character="小", meaning_th="เล็ก", onyomi="しょう", kunyomi="ちい(さい)",
         example_word="小さい", example_reading="ちいさい"),
]


class Command(BaseCommand):
    help = "Seed starter Grammar (JLPT N5 particles) and Kanji (JLPT N5) content for the Flashcard Learning Center."

    def handle(self, *args, **options):
        created_grammar = 0
        for data in GRAMMAR_POINTS:
            _, created = GrammarPoint.objects.get_or_create(
                term=data["term"],
                topic=data["topic"],
                defaults={**data, "language": "japanese", "level": "N5"},
            )
            created_grammar += int(created)

        created_kanji = 0
        for data in KANJI_CHARACTERS:
            _, created = KanjiCharacter.objects.get_or_create(
                character=data["character"],
                defaults={**data, "language": "japanese", "level": "N5"},
            )
            created_kanji += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created_grammar} new GrammarPoint rows "
            f"and {created_kanji} new KanjiCharacter rows "
            f"({len(GRAMMAR_POINTS) - created_grammar} grammar and "
            f"{len(KANJI_CHARACTERS) - created_kanji} kanji already existed)."
        ))
