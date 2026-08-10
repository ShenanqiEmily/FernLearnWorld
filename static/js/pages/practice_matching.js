(function () {
    const items = JSON.parse(document.getElementById("matching-items").textContent) || [];

    function shuffle(array) {
        return array.slice().sort(function () { return Math.random() - 0.5; });
    }

    const fronts = shuffle(items.map(function (item) { return { id: item.id, text: item.front }; }));
    const backs = shuffle(items.map(function (item) { return { id: item.id, text: item.back }; }));

    let matchedCount = 0;
    let wrongAttempts = 0;
    let selectedFront = null;
    let selectedBack = null;

    const frontCol = document.getElementById("matchFrontCol");
    const backCol = document.getElementById("matchBackCol");
    const status = document.getElementById("matchStatus");
    const finishBtn = document.getElementById("matchFinishBtn");

    function renderColumn(container, entries, side) {
        container.innerHTML = "";
        entries.forEach(function (entry) {
            const tile = document.createElement("div");
            tile.className = "fern-match-tile";
            tile.innerText = entry.text;
            tile.dataset.id = entry.id;
            tile.onclick = function () { selectTile(tile, entry.id, side); };
            container.appendChild(tile);
        });
    }

    function selectTile(tile, id, side) {
        if (tile.classList.contains("matched")) return;

        if (side === "front") {
            if (selectedFront) selectedFront.classList.remove("selected");
            selectedFront = tile;
        } else {
            if (selectedBack) selectedBack.classList.remove("selected");
            selectedBack = tile;
        }
        tile.classList.add("selected");

        if (selectedFront && selectedBack) {
            evaluatePair();
        }
    }

    function evaluatePair() {
        const frontId = selectedFront.dataset.id;
        const backId = selectedBack.dataset.id;

        if (frontId === backId) {
            selectedFront.classList.remove("selected");
            selectedBack.classList.remove("selected");
            selectedFront.classList.add("matched");
            selectedBack.classList.add("matched");
            matchedCount++;
            status.innerText = "จับคู่แล้ว " + matchedCount + " / " + items.length;

            selectedFront = null;
            selectedBack = null;

            if (matchedCount >= items.length) {
                const percent = Math.max(
                    0,
                    Math.round((items.length / (items.length + wrongAttempts)) * 100)
                );
                finishBtn.href = finishBtn.dataset.completeUrl + "?score=" + percent;
                finishBtn.innerText = "ส่งคะแนน (" + percent + "%) →";
                finishBtn.style.display = "inline-block";
                status.innerText = "🎉 จับคู่ครบแล้ว! คะแนน " + percent + "%";
            }
        } else {
            wrongAttempts++;
            const wrongFront = selectedFront;
            const wrongBack = selectedBack;
            wrongFront.classList.add("wrong");
            wrongBack.classList.add("wrong");

            setTimeout(function () {
                wrongFront.classList.remove("wrong", "selected");
                wrongBack.classList.remove("wrong", "selected");
            }, 500);

            selectedFront = null;
            selectedBack = null;
        }
    }

    renderColumn(frontCol, fronts, "front");
    renderColumn(backCol, backs, "back");
})();
