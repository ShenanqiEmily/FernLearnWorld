/* =========================================================
   Fern Speech Language Utility
   Shared by any page that uses TTS (speechSynthesis) or STT
   (SpeechRecognition) to speak/listen in the correct language
   for a vocab word, example sentence, etc.

   Detection order:
   1. item.language (e.g. "Chinese" / "Japanese")
   2. pageContext.courseLanguage (course-level fallback)
   3. item.course_code / pageContext.courseCode prefix
      (CN-HSK*, HSK* -> chinese | JP-*, JLPT -> japanese)
   4. item.level (HSK* -> chinese | N1-N5 -> japanese)
   5. defaults to japanese
   ========================================================= */

const FERN_SPEECH_CONFIGS = {
    chinese: {
        ttsLang: "zh-CN",
        recognitionLang: "zh-CN",
        rate: 0.85,
        pitch: 1
    },
    japanese: {
        ttsLang: "ja-JP",
        recognitionLang: "ja-JP",
        rate: 0.85,
        pitch: 1
    }
};

function fernNormalizeLanguageValue(value) {
    const lang = (value || "").toString().trim().toLowerCase();

    if (
        lang === "chinese" ||
        lang === "china" ||
        lang === "cn" ||
        lang === "zh" ||
        lang === "zh-cn" ||
        lang.includes("chinese")
    ) {
        return "chinese";
    }

    if (
        lang === "japanese" ||
        lang === "jp" ||
        lang === "ja" ||
        lang === "ja-jp" ||
        lang.includes("japanese")
    ) {
        return "japanese";
    }

    return "";
}

function fernDetectSpeechLanguage(item, pageContext) {
    const page = pageContext || {};

    const directLanguage =
        fernNormalizeLanguageValue(item && item.language) ||
        fernNormalizeLanguageValue(page.courseLanguage);

    if (directLanguage) {
        return directLanguage;
    }

    const courseCode = (
        (item && item.course_code) ||
        page.courseCode ||
        ""
    ).toString().trim().toUpperCase();

    const level = (
        (item && item.level) ||
        ""
    ).toString().trim().toUpperCase();

    if (
        courseCode.startsWith("CN-HSK") ||
        courseCode.startsWith("HSK") ||
        level.startsWith("HSK")
    ) {
        return "chinese";
    }

    if (
        courseCode.startsWith("JP-") ||
        courseCode.includes("JLPT") ||
        /^N[1-5]$/.test(level)
    ) {
        return "japanese";
    }

    return "japanese";
}

function fernGetSpeechConfig(item, pageContext) {
    const detectedLanguage = fernDetectSpeechLanguage(item, pageContext);
    return FERN_SPEECH_CONFIGS[detectedLanguage] || FERN_SPEECH_CONFIGS.japanese;
}

function fernGetPreferredVoice(lang) {
    if (!window.speechSynthesis || !window.speechSynthesis.getVoices) {
        return null;
    }

    const voices = window.speechSynthesis.getVoices() || [];

    const exactVoice = voices.find(function (voice) {
        return voice.lang === lang;
    });

    if (exactVoice) return exactVoice;

    const languagePrefix = lang.split("-")[0].toLowerCase();

    return voices.find(function (voice) {
        return (voice.lang || "").toLowerCase().startsWith(languagePrefix);
    }) || null;
}

if (window.speechSynthesis && window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = function () {
        window.speechSynthesis.getVoices();
    };
}
