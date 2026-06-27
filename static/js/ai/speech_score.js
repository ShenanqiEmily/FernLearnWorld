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