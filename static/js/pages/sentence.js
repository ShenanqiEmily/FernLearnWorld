

let sentenceIndex = 0;
let currentSentenceText = "";
let recognition = null;

//new code
function normalizeText(text) {
    return (text || "")
        .toLowerCase()
        .replace(/[。、！？!?.,，]/g, "")
        .replace(/\s+/g, "")
        .replace(/-/g, "")
        .replace(/'/g, "")
        .trim();
}

function levenshtein(a, b) {

    a = normalizeText(a);
    b = normalizeText(b);

    const matrix = [];

    for (let i = 0; i <= b.length; i++)
        matrix[i] = [i];

    for (let j = 0; j <= a.length; j++)
        matrix[0][j] = j;

    for (let i = 1; i <= b.length; i++) {

        for (let j = 1; j <= a.length; j++) {

            if (b.charAt(i - 1) === a.charAt(j - 1)) {

                matrix[i][j] = matrix[i - 1][j - 1];

            } else {

                matrix[i][j] = Math.min(

                    matrix[i - 1][j - 1] + 1,

                    matrix[i][j - 1] + 1,

                    matrix[i - 1][j] + 1

                );

            }

        }

    }

    return matrix[b.length][a.length];

}


// function nextSentence() {
//     sentenceIndex = sentenceIndex < sentenceData.length - 1 ? sentenceIndex + 1 : 0;
//     updateSentence();
// }

function resetSentenceUI() {

    // ซ่อนผลการตรวจเสียง
    const result = document.getElementById("sentenceResult");
    if (result) {
        result.style.display = "none";
        result.innerHTML = "";
    }

    // ล้าง AI Tip (ถ้าต้องการ)
    // document.getElementById("aiTip").innerHTML = "";

    // หยุดเสียงที่กำลังเล่น
    window.speechSynthesis.cancel();

    // หยุด Speech Recognition
    if (recognition) {
        recognition.abort();
    }
}

function nextSentence() {

    resetSentenceUI();

    sentenceIndex =
        sentenceIndex < sentenceData.length - 1
            ? sentenceIndex + 1
            : 0;

    updateSentence();
}

function prevSentence() {
    sentenceIndex = sentenceIndex > 0 ? sentenceIndex - 1 : sentenceData.length - 1;
    updateSentence();
}

function jumpToSentence(index) {
    sentenceIndex = index;
    updateSentence();
}

function updateSentence() {
    if (sentenceData.length === 0) return;

    let item = sentenceData[sentenceIndex];

    currentSentenceText = item.sentence;

    document.getElementById("sentenceText").innerText = item.sentence || "-";
    document.getElementById("sentenceReading").innerText = item.sentence_reading || item.reading || "-";
    document.getElementById("sentenceTh").innerText = item.sentence_th || item.meaning_th || "-";
    document.getElementById("sentenceEn").innerText = item.sentence_en || item.meaning_en || "-";

    document.getElementById("sentenceCounter").innerText =
        (sentenceIndex + 1) + " / " + sentenceData.length;

    let progress = ((sentenceIndex + 1) / sentenceData.length) * 100;
    document.getElementById("sentenceProgress").style.width = progress + "%";

    document.getElementById("aiTip").innerText =
        "ประโยคนี้ใช้ฝึกคำว่า 「" + item.word + "」 แปลว่า " + item.meaning_th;

    hideSentenceResult();
}


function speakSentence() {
    if (!currentSentenceText) return;

    if (recognition) {
        try {
            recognition.abort();
        } catch (error) {
            console.warn("Cannot abort old recognition:", error);
        }
    }

    const item = sentenceData[sentenceIndex] || {};
    const speechConfig = fernGetSpeechConfig(item, window.SENTENCE_PAGE);
    console.log('[sentence.js] speakSentence() item.language=', item.language, 'item.course_code=', item.course_code, 'item.level=', item.level, '-> detected config=', speechConfig);

    const utterance = new SpeechSynthesisUtterance(currentSentenceText);
    utterance.lang = speechConfig.ttsLang;
    console.log('[sentence.js] utterance.lang set to', utterance.lang);
    utterance.rate = speechConfig.rate;
    utterance.pitch = speechConfig.pitch;

    const voice = fernGetPreferredVoice(speechConfig.ttsLang);
    if (voice) {
        utterance.voice = voice;
    }

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}



function calculateScore(spoken, expected) {

    spoken = normalizeText(spoken);
    expected = normalizeText(expected);

    if (!spoken || !expected)
        return 0;

    const distance = levenshtein(spoken, expected);

    const maxLen = Math.max(
        spoken.length,
        expected.length
    );

    return Math.round(
        (1 - distance / maxLen) * 100
    );

}

function startSentenceSpeaking() {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showSentenceResult(
            "เบราว์เซอร์นี้ยังไม่รองรับไมค์ แนะนำใช้ Google Chrome",
            "--",
            "warn"
        );
        return;
    }

    // หยุดเสียงที่กำลังเล่นและยกเลิก recognition ค้างเก่า (ถ้ามี) ก่อนเริ่มใหม่
    // ป้องกัน InvalidStateError เวลากดปุ่มซ้ำเร็วๆ หรือมี session ค้างจากรอบก่อน
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }

    if (recognition) {
        try {
            recognition.abort();
        } catch (error) {
            console.warn("Cannot abort old recognition:", error);
        }
    }

    const item = sentenceData[sentenceIndex] || {};
    const speechConfig = fernGetSpeechConfig(item, window.SENTENCE_PAGE);
    console.log('[sentence.js] startSentenceSpeaking() item.language=', item.language, 'item.course_code=', item.course_code, 'item.level=', item.level, '-> detected config=', speechConfig);

    recognition = new SpeechRecognition();
    recognition.lang = speechConfig.recognitionLang;
    console.log('[sentence.js] recognition.lang set to', recognition.lang);
    recognition.interimResults = false;
    recognition.continuous = false;

    showSentenceResult(
        "🎙️ กำลังเตรียมไมค์... รอครึ่งวินาทีแล้วค่อยพูด",
        "--",
        "listen"
    );

    recognition.onresult = function (event) {
        const spoken = event.results[0][0].transcript;

        const japanese = currentSentenceText;

        const romaji =
            sentenceData[sentenceIndex].sentence_reading || "";

        const scoreJapanese =
            calculateScore(
                spoken,
                japanese
            );

        const scoreRomaji =
            calculateScore(
                spoken,
                romaji
            );

        const finalScore =
            Math.max(
                scoreJapanese,
                scoreRomaji
            );

        let feedback = "";
        let resultType = "";

        if (finalScore >= 95) {
            feedback = "🌟 ยอดเยี่ยมมาก! ออกเสียงชัดสุด ๆ";
            resultType = "good";
        } else if (finalScore >= 85) {
            feedback = "✅ ดีมาก! พูดได้ชัดเจน";
            resultType = "good";
        } else if (finalScore >= 70) {
            feedback = "👍 ผ่านแล้ว ลองพูดช้าลงอีกนิดจะดีขึ้น";
            resultType = "good";
        } else {
            feedback = "🔄 ลองอีกครั้ง ฟังเสียงก่อนแล้วพูดตามช้า ๆ";
            resultType = "warn";
        }

        showSentenceResult(

            `🎤 คุณพูดว่า

                    ${spoken}

                    <hr>

                    📖 ประโยค

                    ${japanese}

                    📝 Romaji

                    ${romaji}

                    `,

            finalScore + "%",

            resultType

        );
    };

    recognition.onerror = function (event) {
        let message = "ไมค์ไม่ทำงาน หรือยังไม่ได้กดอนุญาตไมค์";

        if (event.error === "no-speech") {
            message = "ไม่ได้ยินเสียง ลองกดใหม่ แล้วเว้นจังหวะครึ่งวินาทีก่อนพูด";
        } else if (event.error === "audio-capture") {
            message = "ไม่พบไมโครโฟน กรุณาเช็กไมค์";
        } else if (event.error === "not-allowed") {
            message = "ยังไม่ได้อนุญาตไมค์ กรุณากด Allow";
        } else if (event.error === "network") {
            message = "ระบบฟังเสียงมีปัญหาเครือข่าย ลองใหม่อีกครั้ง";
        } else if (event.error === "language-not-supported") {
            message = "เบราว์เซอร์นี้ยังไม่รองรับการฟังเสียงภาษานี้ แนะนำใช้ Google Chrome เวอร์ชันล่าสุด";
        }

        showSentenceResult(message, "--", "warn");
    };

    recognition.onend = function () {
        console.log("Sentence recognition ended");
    };

    setTimeout(function () {
        try {
            recognition.start();
            console.log("Recognition language:", speechConfig.recognitionLang);
        } catch (error) {
            console.warn("Recognition start error:", error);
            showSentenceResult(
                "เริ่มไมค์ไม่สำเร็จ กรุณาลองกดใหม่อีกครั้ง",
                "--",
                "warn"
            );
        }
    }, 500);
}

function showSentenceResult(text, score, type) {
    const box = document.getElementById("sentenceResult");
    if (!box) return;

    box.style.display = "block";
    box.innerHTML = `
        <b>${text}</b><br>
        <span>คะแนน: ${score}</span>
    `;

    if (type === "good") {
        box.style.background = "#ecfdf5";
        box.style.color = "#047857";
    } else if (type === "warn") {
        box.style.background = "#fff7ed";
        box.style.color = "#c2410c";
    } else {
        box.style.background = "#eff6ff";
        box.style.color = "#2563eb";
    }
}

updateSentence();
