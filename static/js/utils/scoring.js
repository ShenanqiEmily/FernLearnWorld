/* =========================================================
   Fern Scoring Utility
   Shared normalize/Levenshtein/score helpers for any page that
   grades a typed or spoken answer against an expected string
   (or a list of accepted alternatives).
   ========================================================= */

function fernNormalizeText(text) {
    return (text || "")
        .toLowerCase()
        .replace(/[。、！？!?.,，]/g, "")
        .replace(/\s+/g, "")
        .replace(/-/g, "")
        .replace(/'/g, "")
        .replace(/’/g, "")
        .trim();
}

function fernLevenshtein(a, b) {
    a = fernNormalizeText(a);
    b = fernNormalizeText(b);

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

function fernCalculateScore(spoken, expected) {
    spoken = fernNormalizeText(spoken);
    expected = fernNormalizeText(expected);

    if (!spoken || !expected) return 0;

    const distance = fernLevenshtein(spoken, expected);
    const maxLen = Math.max(spoken.length, expected.length);

    return Math.round((1 - distance / maxLen) * 100);
}

/** Best score of `answer` against a list of accepted strings. */
function fernBestScore(answer, acceptedForms) {
    let best = 0;
    (acceptedForms || []).forEach(function (form) {
        const score = fernCalculateScore(answer, form);
        if (score > best) best = score;
    });
    return best;
}
