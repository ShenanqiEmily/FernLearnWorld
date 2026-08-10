let currentIndex = 0;
let recognition = null;

function updateVocabCard() {
    if (!Array.isArray(vocabs) || vocabs.length === 0) return;

    const vocab = vocabs[currentIndex];

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

    const progress = ((currentIndex + 1) / vocabs.length) * 100;
    document.getElementById("vocabProgress").style.width = progress + "%";

    hideSpeechResult();
}

function toggleClass(selector) {
    document.querySelectorAll(selector).forEach(function (el) {
        el.style.display = el.style.display === "none" ? "" : "none";
    });
}

/* =========================================================
   Language detection for TTS / Speech Recognition is shared
   via static/js/utils/speech-lang.js (loaded before this file).
   window.VOCAB_PAGE = {courseCode, courseLanguage} is set in
   vocab_card.html as the page-level fallback.
   ========================================================= */

function getSpeechConfig(vocab) {
    return fernGetSpeechConfig(vocab, window.VOCAB_PAGE);
}

function getPreferredVoice(lang) {
    return fernGetPreferredVoice(lang);
}

function speakText(text, vocab) {
    if (!text) return;

    const currentVocab = vocab || vocabs[currentIndex] || {};
    const speechConfig = getSpeechConfig(currentVocab);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechConfig.ttsLang;
    utterance.rate = speechConfig.rate;
    utterance.pitch = speechConfig.pitch;

    const voice = getPreferredVoice(speechConfig.ttsLang);
    if (voice) {
        utterance.voice = voice;
    }

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);

    console.log("TTS language:", speechConfig.ttsLang);
}

function speakCurrentWord() {
    if (!Array.isArray(vocabs) || vocabs.length === 0) return;

    const vocab = vocabs[currentIndex];
    speakText(vocab.word, vocab);
}

function speakCurrentSentence() {
    if (!Array.isArray(vocabs) || vocabs.length === 0) return;

    const vocab = vocabs[currentIndex];
    speakText(vocab.example_sentence, vocab);
}

function resetVocabUI() {
    hideSpeechResult();

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
}

function nextVocab() {
    resetVocabUI();

    if (currentIndex < vocabs.length - 1) {
        currentIndex++;
        updateVocabCard();
    }
}

function prevVocab() {
    resetVocabUI();

    if (currentIndex > 0) {
        currentIndex--;
        updateVocabCard();
    }
}

function jumpToVocab(index) {
    resetVocabUI();

    if (index >= 0 && index < vocabs.length) {
        currentIndex = index;
        updateVocabCard();
    }
}

function normalizeText(text) {
    return (text || "")
        .toLowerCase()
        .replace(/[。、！？!?.,，]/g, "")
        .replace(/\s+/g, "")
        .replace(/-/g, "")
        .replace(/'/g, "")
        .replace(/’/g, "")
        .trim();
}

function levenshtein(a, b) {
    a = normalizeText(a);
    b = normalizeText(b);

    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

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

function calculateScore(spoken, expected) {
    spoken = normalizeText(spoken);
    expected = normalizeText(expected);

    if (!spoken || !expected) return 0;

    const distance = levenshtein(spoken, expected);
    const maxLen = Math.max(spoken.length, expected.length);

    return Math.round((1 - distance / maxLen) * 100);
}

function splitAcceptedForms(value) {
    if (!value) return [];

    return value
        .toString()
        .split(/[,、/|]/)
        .map(function (item) {
            return item.trim();
        })
        .filter(Boolean);
}

function getAcceptedWordForms(vocab) {
    let forms = [];

    const rawForms = [
        vocab.word,
        vocab.reading,
        vocab.pinyin,
        vocab.romaji,
        vocab.kana,
        vocab.kanji,
        vocab.word_kana,
        vocab.word_kanji
    ];

    rawForms.forEach(function (form) {
        if (form) {
            forms.push(form);
        }
    });

    const aliasFields = [
        vocab.speech_aliases,
        vocab.aliases,
        vocab.accepted_forms
    ];

    aliasFields.forEach(function (field) {
        splitAcceptedForms(field).forEach(function (alias) {
            forms.push(alias);
        });
    });

    return forms
        .map(normalizeText)
        .filter(Boolean)
        .filter(function (item, index, array) {
            return array.indexOf(item) === index;
        });
}

function calculateBestScore(spoken, acceptedForms) {
    let bestScore = 0;
    let matchedForm = "";

    acceptedForms.forEach(function (expectedForm) {
        const score = calculateScore(spoken, expectedForm);

        if (score > bestScore) {
            bestScore = score;
            matchedForm = expectedForm;
        }
    });

    return {
        score: bestScore,
        matchedForm: matchedForm
    };
}

function getWordFeedback(finalScore) {
    if (finalScore >= 90) {
        return {
            text: "🌟 ยอดเยี่ยมมาก! ออกเสียงชัดเจน",
            type: "good"
        };
    }

    if (finalScore >= 75) {
        return {
            text: "✅ ดีมาก ผ่านแล้ว",
            type: "good"
        };
    }

    if (finalScore >= 55) {
        return {
            text: "👍 ใกล้เคียงแล้ว ลองพูดช้าลงอีกนิด",
            type: "good"
        };
    }

    return {
        text: "🔄 ยังไม่ค่อยตรง ลองฟังเสียงแล้วพูดตามอีกครั้ง",
        type: "warn"
    };
}

function startWordSpeaking() {
    if (!Array.isArray(vocabs) || vocabs.length === 0) return;

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

    const vocab = vocabs[currentIndex];
    const targetWord = vocab.word || "";
    const targetReading = vocab.reading || "";
    const targetPinyin = vocab.pinyin || "";
    const acceptedForms = getAcceptedWordForms(vocab);
    const speechConfig = getSpeechConfig(vocab);

    recognition = new SpeechRecognition();
    recognition.lang = speechConfig.recognitionLang;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 5;

    showSpeechResult(
        "🎙️ กำลังเตรียมไมค์... รอครึ่งวินาทีแล้วค่อยพูด: " + targetWord,
        "--",
        "listen"
    );

    recognition.onresult = function (event) {
        let bestSpoken = "";
        let bestScore = 0;
        let bestMatchedForm = "";
        let bestConfidence = 0;

        const alternatives = Array.from(event.results[0]);

        alternatives.forEach(function (result) {
            const spoken = result.transcript || "";
            const confidence = result.confidence || 0;
            const scoreResult = calculateBestScore(spoken, acceptedForms);

            if (
                scoreResult.score > bestScore ||
                (
                    scoreResult.score === bestScore &&
                    confidence > bestConfidence
                )
            ) {
                bestScore = scoreResult.score;
                bestSpoken = spoken;
                bestMatchedForm = scoreResult.matchedForm;
                bestConfidence = confidence;
            }
        });

        const feedback = getWordFeedback(bestScore);

        if (typeof window.onWordSpeakingScored === "function") {
            window.onWordSpeakingScored(currentIndex, bestScore, targetWord);
        }

        showSpeechResult(
            `
            🎤 คุณพูดว่า<br>
            ${bestSpoken || "-"}

            <hr>

            📖 คำศัพท์<br>
            ${targetWord || "-"}

            <br><br>

            📝 Reading<br>
            ${targetReading || "-"}

            ${targetPinyin ? "<br><br>🔤 Pinyin / Romaji<br>" + targetPinyin : ""}

            <br><br>

            ✅ ระบบยอมรับ<br>
            ${acceptedForms.join(" / ") || "-"}

            <br><br>

            🎯 ตรงกับรูปแบบ<br>
            ${bestMatchedForm || "-"}

            <hr>

            ${feedback.text}
            `,
            bestScore + "%",
            feedback.type
        );

        console.log("Recognition language:", speechConfig.recognitionLang);
        console.log("Target word:", targetWord);
        console.log("Target reading:", targetReading);
        console.log("Target pinyin:", targetPinyin);
        console.log("Accepted forms:", acceptedForms);
        console.log("Best spoken:", bestSpoken);
        console.log("Best matched form:", bestMatchedForm);
        console.log("Best score:", bestScore);
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
        }

        showSpeechResult(
            message,
            "--",
            "warn"
        );
    };

    recognition.onend = function () {
        console.log("Speech recognition ended");
    };

    setTimeout(function () {
        try {
            recognition.start();
            console.log("Recognition language:", speechConfig.recognitionLang);
        } catch (error) {
            console.warn("Recognition start error:", error);
        }
    }, 500);
}

function hideSpeechResult() {
    const box = document.getElementById("speechResultBox");

    if (box) {
        box.style.display = "none";
        box.innerHTML = "";
    }
}

function showSpeechResult(text, score, type) {
    const box = document.getElementById("speechResultBox");

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