(function () {
    const items = JSON.parse(document.getElementById("mc-items").textContent) || [];

    let index = 0;
    let score = 0;
    let answered = 0;
    let locked = false;

    const frontText = document.getElementById("mcFrontText");
    const frontChar = document.getElementById("mcFrontChar");
    const audioBtn = document.getElementById("mcAudioBtn");
    const optionsBox = document.getElementById("mcOptions");
    const resultBox = document.getElementById("mcResult");
    const scoreBox = document.getElementById("mcScoreBox");
    const counter = document.getElementById("mcCounter");
    const progress = document.getElementById("mcProgress");
    const finishBtn = document.getElementById("mcFinishBtn");

    function currentItem() {
        return items[index];
    }

    window.mcPlayAudio = function () {
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

        frontText.style.display = "none";
        frontChar.style.display = "none";
        audioBtn.style.display = "none";

        if (item.front_type === "character") {
            frontChar.innerText = item.front;
            frontChar.style.display = "block";
        } else if (item.front_type === "audio") {
            audioBtn.style.display = "inline-block";
            setTimeout(window.mcPlayAudio, 300);
        } else {
            frontText.innerText = item.front;
            frontText.style.display = "block";
        }

        resultBox.style.display = "none";
        counter.innerText = (index + 1) + " / " + items.length;
        progress.style.width = Math.round((index / items.length) * 100) + "%";

        optionsBox.innerHTML = "";
        item.options.forEach(function (option) {
            const btn = document.createElement("button");
            btn.className = "fern-option";
            btn.innerText = option;
            btn.onclick = function () { checkAnswer(btn, option); };
            optionsBox.appendChild(btn);
        });
    }

    function checkAnswer(button, answer) {
        if (locked) return;
        locked = true;
        answered++;

        const item = currentItem();
        const correct = item.correct;

        document.querySelectorAll(".fern-option").forEach(function (btn) {
            if (btn.innerText === correct) btn.classList.add("correct");
        });

        if (answer === correct) {
            button.classList.add("correct");
            resultBox.className = "fern-result correct";
            resultBox.innerText = "✅ ถูกต้อง!";
            score++;
        } else {
            button.classList.add("wrong");
            resultBox.className = "fern-result wrong";
            resultBox.innerText = "❌ คำตอบที่ถูกคือ: " + correct;
        }
        resultBox.style.display = "block";

        const percent = Math.round((score / answered) * 100);
        scoreBox.innerText = "คะแนน: " + percent + "% (" + score + "/" + answered + ")";

        progress.style.width = Math.round(((index + 1) / items.length) * 100) + "%";

        setTimeout(function () {
            if (index < items.length - 1) {
                index++;
                renderItem();
            } else {
                const finalUrl = finishBtn.dataset.completeUrl + "?score=" + percent;
                finishBtn.href = finalUrl;
                finishBtn.style.display = "inline-block";
                finishBtn.innerText = "ส่งคะแนน (" + percent + "%) →";
            }
        }, 1400);
    }

    renderItem();
})();
