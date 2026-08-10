window.practiceScores = {};

window.onWordSpeakingScored = function (index, score) {
    if (!Array.isArray(vocabs) || vocabs.length === 0) return;

    window.practiceScores[index] = score;

    const attempted = Object.keys(window.practiceScores).length;
    const counter = document.getElementById("practiceSpeakingCounter");

    if (counter) {
        counter.innerText = attempted + " / " + vocabs.length;
    }

    if (attempted >= vocabs.length) {
        const total = Object.values(window.practiceScores).reduce(function (a, b) {
            return a + b;
        }, 0);
        const avg = Math.round(total / vocabs.length);

        const btn = document.getElementById("finishSpeakingBtn");
        if (btn) {
            btn.href = btn.dataset.completeUrl + "?score=" + avg;
            btn.style.display = "inline-flex";
        }
    }
};
