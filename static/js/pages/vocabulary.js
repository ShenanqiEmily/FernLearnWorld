
let currentIndex = 0;

function updateVocabCard() {
    if (vocabs.length === 0) return;

    let vocab = vocabs[currentIndex];

    document.getElementById("vocabWord").innerText = vocab.word || "-";
    document.getElementById("vocabReading").innerText = vocab.reading || "-";
    document.getElementById("vocabMeaningTh").innerText = vocab.meaning_th || "-";
    document.getElementById("vocabMeaningEn").innerText = vocab.meaning_en || "-";

    document.getElementById("vocabExampleSentence").innerText = vocab.example_sentence || "-";
    document.getElementById("vocabExampleReading").innerText = vocab.example_reading || "";
    document.getElementById("vocabExampleTh").innerText = vocab.example_translation_th || "";
    document.getElementById("vocabExampleEn").innerText = vocab.example_translation_en || "";

    document.getElementById("vocabCounter").innerText =
        (currentIndex + 1) + " / " + vocabs.length;

    let progress = ((currentIndex + 1) / vocabs.length) * 100;
    document.getElementById("vocabProgress").style.width = progress + "%";
    hideSpeechResult();
}

function toggleClass(selector) {
    document.querySelectorAll(selector).forEach(function (el) {
        el.style.display = el.style.display === "none" ? "" : "none";
    });
}

function speakText(text) {
    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ja-JP";
    utterance.rate = 0.85;
    utterance.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

function speakCurrentWord() {
    if (vocabs.length === 0) return;
    speakText(vocabs[currentIndex].word);
}

function speakCurrentSentence() {
    if (vocabs.length === 0) return;
    speakText(vocabs[currentIndex].example_sentence);
}


let recognition = null;

function resetVocabUI() {

    // ซ่อนผลการตรวจเสียง
    const result = document.getElementById("speechResultBox");
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

function nextVocab() {

    resetVocabUI();

    if (currentIndex < vocabs.length - 1) {
        currentIndex++;
        updateVocabCard();
    }
}

function prevVocab() {
    if (currentIndex > 0) {
        currentIndex--;
        updateVocabCard();
    }
}

function jumpToVocab(index) {
    currentIndex = index;
    updateVocabCard();
}



function startWordSpeaking() {
    if (vocabs.length === 0) return;

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showSpeechResult(
            "เบราว์เซอร์นี้ยังไม่รองรับไมค์ แนะนำใช้ Google Chrome",
            "--",
            "warn"
        );
        return;
    }

    const vocab = vocabs[currentIndex];
    const targetWord = vocab.word;
    const targetReading = vocab.reading;

    recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.interimResults = false;
    recognition.continuous = false;

    showSpeechResult("กำลังฟัง... พูดเฉพาะคำนี้: " + targetWord, "--", "listen");

    recognition.start();

    recognition.onresult = function (event) {
        const spoken = event.results[0][0].transcript;

        const scoreWord = similarity(spoken, targetWord);
        const scoreReading = similarity(spoken, targetReading);
        const finalScore = Math.max(scoreWord, scoreReading);

        if (finalScore >= 70) {
            showSpeechResult(
                "คุณพูดว่า: " + spoken,
                finalScore + "% ผ่าน ✅",
                "good"
            );
        } else {
            showSpeechResult(
                "คุณพูดว่า: " + spoken + "<br>ควรพูด: " + targetWord + " / " + targetReading,
                finalScore + "% ลองใหม่อีกครั้ง",
                "warn"
            );
        }
    };

    recognition.onerror = function () {
        showSpeechResult(
            "ไมค์ไม่ทำงาน หรือยังไม่ได้กดอนุญาตไมค์",
            "--",
            "warn"
        );
    };
}

function hideSpeechResult() {
    const box = document.getElementById("speechResultBox");
    if (box) {
        box.style.display = "none";
        box.innerHTML = "";
    }
}

function showSpeechResult(text, score, type) {
    let box = document.getElementById("speechResultBox");
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

function showSpeechResult(text, score, type) {
    let box = document.getElementById("speechResultBox");

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
updateVocabCard();
