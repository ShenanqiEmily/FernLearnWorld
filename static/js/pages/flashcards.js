let fcCards = [];
let fcIndex = 0;

function fcInit() {
    const dataEl = document.getElementById("flashcard-data");
    if (!dataEl) return;

    fcCards = JSON.parse(dataEl.textContent) || [];
    fcIndex = 0;
    fcRender();
}

function fcGetCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}

function fcRender() {
    if (fcIndex >= fcCards.length) {
        fcShowDone();
        return;
    }

    const card = fcCards[fcIndex];
    const cardEl = document.getElementById("fcCard");
    cardEl.classList.remove("flipped");

    document.getElementById("fcFrontMain").innerText = card.front_main || "-";
    document.getElementById("fcFrontSub").innerText = card.front_sub || "";
    document.getElementById("fcBackMain").innerText = card.back_main || "-";
    document.getElementById("fcBackSub").innerText = card.back_sub || "";

    document.getElementById("fcExampleSentence").innerText = card.example_sentence || "";
    document.getElementById("fcExampleReading").innerText = card.example_reading || "";
    document.getElementById("fcExampleTranslation").innerText = card.example_translation || "";

    document.getElementById("fcExampleBox").style.display = card.example_sentence ? "block" : "none";

    document.getElementById("fcProgress").innerText = (fcIndex + 1) + " / " + fcCards.length;
}

function flashcardFlip() {
    document.getElementById("fcCard").classList.toggle("flipped");
}

function flashcardSpeak() {
    if (fcIndex >= fcCards.length) return;

    const card = fcCards[fcIndex];
    const text = card.example_sentence || card.front_main;
    if (!text || !window.speechSynthesis) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = card.tts_lang || "ja-JP";
    utterance.rate = 0.85;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

function flashcardGrade(quality) {
    if (fcIndex >= fcCards.length) return;

    const card = fcCards[fcIndex];
    const csrftoken = fcGetCookie("csrftoken");

    fetch(window.FC_REVIEW_URL || "/flashcards/review/", {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            category: card.category,
            object_id: card.object_id,
            quality: quality,
        }),
    })
        .catch(function (error) {
            console.warn("Flashcard review save failed:", error);
        })
        .finally(function () {
            fcIndex++;
            fcRender();
        });
}

function fcShowDone() {
    const cardWrap = document.querySelector(".fc-card-wrap");
    const doneState = document.getElementById("fcDoneState");

    if (cardWrap) cardWrap.style.display = "none";
    if (doneState) doneState.style.display = "block";
}

fcInit();
