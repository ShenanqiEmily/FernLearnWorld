(function () {
    const items = JSON.parse(document.getElementById("sb-items").textContent) || [];

    let index = 0;
    let correctCount = 0;
    let answeredCount = 0;
    let picked = [];
    let poolTiles = [];

    const termBox = document.getElementById("sbTerm");
    const meaningBox = document.getElementById("sbMeaning");
    const answerBox = document.getElementById("sbAnswer");
    const poolBox = document.getElementById("sbPool");
    const resultBox = document.getElementById("sbResult");
    const scoreBox = document.getElementById("sbScoreBox");
    const counter = document.getElementById("sbCounter");
    const progress = document.getElementById("sbProgress");
    const finishBtn = document.getElementById("sbFinishBtn");

    function currentItem() {
        return items[index];
    }

    function renderAnswer() {
        answerBox.innerHTML = "";
        picked.forEach(function (tileIndex) {
            const span = document.createElement("span");
            span.className = "fern-sb-tile";
            span.innerText = currentItem().tokens[tileIndex];
            span.onclick = function () { removeFromAnswer(tileIndex); };
            answerBox.appendChild(span);
        });
    }

    function removeFromAnswer(tileIndex) {
        picked = picked.filter(function (i) { return i !== tileIndex; });
        renderAnswer();
        syncPool();
    }

    function syncPool() {
        poolTiles.forEach(function (tile, i) {
            tile.classList.toggle("used", picked.indexOf(i) !== -1);
        });
    }

    function renderItem() {
        const item = currentItem();
        picked = [];

        termBox.innerText = item.term;
        meaningBox.innerText = item.meaning ? "แปลว่า: " + item.meaning : "";
        resultBox.style.display = "none";

        poolBox.innerHTML = "";
        poolTiles = item.tokens.map(function (token, i) {
            const tile = document.createElement("span");
            tile.className = "fern-sb-tile";
            tile.innerText = token;
            tile.onclick = function () { addToAnswer(i); };
            poolBox.appendChild(tile);
            return tile;
        });

        renderAnswer();
        counter.innerText = (index + 1) + " / " + items.length;
        progress.style.width = Math.round((index / items.length) * 100) + "%";
    }

    function addToAnswer(tileIndex) {
        if (picked.indexOf(tileIndex) !== -1) return;
        picked.push(tileIndex);
        renderAnswer();
        syncPool();
    }

    window.sbUndo = function () {
        picked.pop();
        renderAnswer();
        syncPool();
    };

    window.sbSubmit = function () {
        const item = currentItem();
        const built = picked.map(function (i) { return item.tokens[i]; }).join("");

        answeredCount++;
        const isCorrect = built === item.answer;
        if (isCorrect) correctCount++;

        resultBox.className = "fern-result " + (isCorrect ? "good" : "warn");
        resultBox.innerHTML = isCorrect
            ? "✅ ถูกต้อง!"
            : "🔄 คำตอบที่ถูกคือ: " + item.answer;
        resultBox.style.display = "block";

        const percent = Math.round((correctCount / answeredCount) * 100);
        scoreBox.innerText = "คะแนน: " + percent + "% (" + correctCount + "/" + answeredCount + ")";

        progress.style.width = Math.round(((index + 1) / items.length) * 100) + "%";

        setTimeout(function () {
            if (index < items.length - 1) {
                index++;
                renderItem();
            } else {
                finishBtn.href = finishBtn.dataset.completeUrl + "?score=" + percent;
                finishBtn.innerText = "ส่งคะแนน (" + percent + "%) →";
                finishBtn.style.display = "inline-block";
            }
        }, 1600);
    };

    renderItem();
})();
