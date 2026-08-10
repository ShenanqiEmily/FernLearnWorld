(function () {
    const items = JSON.parse(document.getElementById("typing-items").textContent) || [];

    let index = 0;
    let totalScore = 0;
    let answeredCount = 0;
    let locked = false;

    const promptBox = document.getElementById("typingPrompt");
    const audioBtn = document.getElementById("typingAudioBtn");
    const input = document.getElementById("typingInput");
    const resultBox = document.getElementById("typingResult");
    const scoreBox = document.getElementById("typingScoreBox");
    const counter = document.getElementById("typingCounter");
    const progress = document.getElementById("typingProgress");
    const finishBtn = document.getElementById("typingFinishBtn");

    function currentItem() {
        return items[index];
    }

    window.typingPlayAudio = function () {
        const item = currentItem();
        if (!item || !item.tts_text) return;

        const config = fernGetSpeechConfig(item, {});
        const utterance = new SpeechSynthesisUtterance(item.tts_text);
        utterance.lang = config.ttsLang;
        utterance.rate = config.rate;
        const voice = fernGetPreferredVoice(config.ttsLang);
        if (voice) utterance.voice = voice;

        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    };

    function renderItem() {
        locked = false;
        const item = currentItem();

        input.value = "";
        input.disabled = false;
        resultBox.style.display = "none";

        if (item.prompt_type === "audio") {
            audioBtn.style.display = "inline-block";
            promptBox.innerText = "ฟังเสียง แล้วพิมพ์สิ่งที่ได้ยิน";
            setTimeout(window.typingPlayAudio, 300);
        } else {
            audioBtn.style.display = "none";
            promptBox.innerText = item.prompt;
        }

        counter.innerText = (index + 1) + " / " + items.length;
        progress.style.width = Math.round((index / items.length) * 100) + "%";
        input.focus();
    }

    window.typingSubmit = function () {
        if (locked) return;

        const item = currentItem();
        const answer = input.value.trim();
        if (!answer) return;

        locked = true;
        input.disabled = true;
        answeredCount++;

        const accepted = [item.answer].concat(item.aliases || []);
        const score = fernBestScore(answer, accepted);
        totalScore += score;

        if (score >= 70) {
            resultBox.className = "fern-result good";
            resultBox.innerHTML = "✅ ถูกต้อง! (" + score + "%)<br>คำตอบ: " + item.answer;
        } else {
            resultBox.className = "fern-result warn";
            resultBox.innerHTML = "🔄 ยังไม่ตรง (" + score + "%)<br>คำตอบที่ถูกคือ: " + item.answer;
        }
        resultBox.style.display = "block";

        const avg = Math.round(totalScore / answeredCount);
        scoreBox.innerText = "คะแนนเฉลี่ย: " + avg + "%";

        progress.style.width = Math.round(((index + 1) / items.length) * 100) + "%";

        setTimeout(function () {
            if (index < items.length - 1) {
                index++;
                renderItem();
            } else {
                finishBtn.href = finishBtn.dataset.completeUrl + "?score=" + avg;
                finishBtn.innerText = "ส่งคะแนน (" + avg + "%) →";
                finishBtn.style.display = "inline-block";
            }
        }, 1600);
    };

    input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            window.typingSubmit();
        }
    });

    renderItem();
})();
