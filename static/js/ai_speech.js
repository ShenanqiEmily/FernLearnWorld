// ===============================
// FernLearn AI Speech Engine v1
// ===============================

//move to ai/speech.js
function normalizeText(text) {

    return (text || "")
        .toLowerCase()
        .replace(/[。、！？!?.,，]/g, "")
        .replace(/\s+/g, "")
        .replace(/-/g, "")
        .replace(/'/g, "")
        .trim();

}
//move

// -----------------------------
//move to ai/speech_score.js
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

            }

            else {

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


// -----------------------------

//move to ai/speech_scrore.js
function calculateScore(spoken,expected){

    const lang = detectLanguage(expected);

    if(lang==="ja"){

        spoken = cleanJapanese(spoken);

        expected = cleanJapanese(expected);

    }

    else{

        spoken = normalizeText(spoken);

        expected = normalizeText(expected);

    }

    if(!spoken || !expected){

        return 0;

    }

    const distance = levenshtein(spoken,expected);

    const maxLength=Math.max(

        spoken.length,

        expected.length

    );

    return Math.round(

        (1-distance/maxLength)*100

    );

}

function normalizeJapanese(text) {

    text = normalizeText(text);

    return text

        .replace(/です/g, "")

        .replace(/ます/g, "")

        .replace(/を/g, "")

        .replace(/は/g, "")

        .replace(/が/g, "");

}

// ===============================
// Detect Language
// ===============================

function detectLanguage(text){

    if(/[一-龯ぁ-んァ-ン]/.test(text)){
        return "ja";
    }

    if(/[\u4e00-\u9fff]/.test(text)){
        return "zh";
    }

    return "en";

}
function cleanJapanese(text){

    return normalizeText(text)

        .replace(/です/g,"")
        .replace(/ます/g,"")
        .replace(/でした/g,"")
        .replace(/でしたか/g,"")
        .replace(/を/g,"")
        .replace(/は/g,"")
        .replace(/が/g,"");

}