(function () {
    const modesEl = document.getElementById("practice-modes");
    const orderEl = document.getElementById("practice-mode-order");
    const percentsEl = document.getElementById("practice-mode-percents");
    const urlsEl = document.getElementById("practice-mode-urls");
    const grid = document.getElementById("practiceHubGrid");

    if (!modesEl || !orderEl || !percentsEl || !grid) return;

    const modes = JSON.parse(modesEl.textContent) || {};
    const order = JSON.parse(orderEl.textContent) || [];
    const percents = JSON.parse(percentsEl.textContent) || {};
    const urls = urlsEl ? (JSON.parse(urlsEl.textContent) || {}) : {};

    const difficultyLabels = {
        beginner: "เริ่มต้น",
        intermediate: "ปานกลาง",
        advanced: "ยาก",
    };

    function buildCard(key) {
        const mode = modes[key];
        if (!mode) return "";

        const percent = percents[key] || 0;
        const difficultyLabel = difficultyLabels[mode.difficulty] || mode.difficulty;
        const url = urls[key];

        const inner = `
            <div class="fern-card-icon">${mode.icon}</div>
            <div class="fern-card-label">${mode.label}</div>
            <div class="fern-card-desc">${mode.description || ""}</div>
            <div class="fern-card-chips">
                <span class="fern-chip fern-chip-difficulty">${difficultyLabel}</span>
                <span class="fern-chip fern-chip-xp">+${mode.xp_reward} XP</span>
            </div>
            <div class="fern-card-progress-bar">
                <span style="width:${percent}%"></span>
            </div>
            <div class="fern-card-progress-label">${percent}% สำเร็จ</div>
        `;

        if (mode.playable && url) {
            return `<a class="fern-practice-card" href="${url}">${inner}</a>`;
        }

        return `
            <div class="fern-practice-card disabled">
                <span class="fern-soon-ribbon">เร็วๆ นี้</span>
                ${inner}
            </div>
        `;
    }

    grid.innerHTML = order.map(buildCard).join("");
})();
