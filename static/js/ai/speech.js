function normalizeText(text) {

    return (text || "")
        .toLowerCase()
        .replace(/[。、！？!?.,，]/g, "")
        .replace(/\s+/g, "")
        .replace(/-/g, "")
        .replace(/'/g, "")
        .trim();

}
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