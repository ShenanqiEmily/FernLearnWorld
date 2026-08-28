let atModes = {};
let atModeOrder = [];
let atCurrentMode = null;
let atHistories = {};
let atRecognition = null;
let atSending = false;

function atGetCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}

function atInit() {
    const modesEl = document.getElementById("ai-tutor-modes");
    const orderEl = document.getElementById("ai-tutor-mode-order");
    if (!modesEl || !orderEl) return;

    atModes = JSON.parse(modesEl.textContent) || {};
    atModeOrder = JSON.parse(orderEl.textContent) || [];

    atModeOrder.forEach(function (key) {
        atHistories[key] = [];
    });

    atRenderModeList();
    if (atModeOrder.length > 0) {
        atSelectMode(atModeOrder[0]);
    }

    document.getElementById("atSendBtn").addEventListener("click", atSendCurrentInput);
    document.getElementById("atTextarea").addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            atSendCurrentInput();
        }
    });
    document.getElementById("atMicBtn").addEventListener("click", atToggleMic);
}

function atRenderModeList() {
    const list = document.getElementById("atModeList");
    list.innerHTML = "";

    atModeOrder.forEach(function (key) {
        const mode = atModes[key];
        const btn = document.createElement("button");
        btn.className = "at-mode-item" + (key === atCurrentMode ? " active" : "");
        btn.innerHTML =
            '<span class="at-mode-icon">' + mode.icon + "</span>" +
            "<span>" + mode.label + '<small class="at-mode-desc">' + mode.description + "</small></span>";
        btn.addEventListener("click", function () {
            atSelectMode(key);
        });
        list.appendChild(btn);
    });
}

function atSelectMode(key) {
    atCurrentMode = key;
    atRenderModeList();
    atRenderMessages();
    atRenderSuggestedPrompts();
}

function atRenderSuggestedPrompts() {
    const row = document.getElementById("atSuggestedRow");
    row.innerHTML = "";

    const mode = atModes[atCurrentMode];
    if (!mode || !mode.suggested_prompts) return;

    mode.suggested_prompts.forEach(function (prompt) {
        const chip = document.createElement("button");
        chip.className = "at-chip";
        chip.innerText = prompt;
        chip.addEventListener("click", function () {
            atSendMessage(prompt);
        });
        row.appendChild(chip);
    });
}

function atRenderMessages() {
    const box = document.getElementById("atMessages");
    box.innerHTML = "";

    (atHistories[atCurrentMode] || []).forEach(function (item) {
        box.appendChild(atBuildBubble(item.role, item.content, item.isError, item.isUpsell));
    });

    box.scrollTop = box.scrollHeight;
}

function atBuildBubble(role, text, isError, isUpsell) {
    const wrap = document.createElement("div");
    wrap.className = "fern-message " + (role === "user" ? "user" : "ai");

    const bubble = document.createElement("div");
    // isUpsell (daily free-tier limit reached) is deliberately styled apart
    // from isError (something actually broke) — it's an invitation, not a
    // failure, so it shouldn't look alarming like a red error bubble.
    bubble.className = "fern-bubble" + (isError ? " at-error-bubble" : "") + (isUpsell ? " at-upsell-bubble" : "");
    bubble.innerText = text;

    if (isUpsell) {
        const upgradeBtn = document.createElement("a");
        upgradeBtn.className = "at-upsell-btn";
        upgradeBtn.href = window.SUBSCRIBE_URL || "/subscribe/";
        upgradeBtn.innerText = "อัพเกรดเลย →";
        bubble.appendChild(document.createElement("br"));
        bubble.appendChild(upgradeBtn);
    }

    if (role !== "user" && !isError && !isUpsell) {
        const soundBtn = document.createElement("button");
        soundBtn.className = "at-sound-btn";
        soundBtn.innerText = "🔊 ฟังเสียงคำตอบ";
        soundBtn.addEventListener("click", function () {
            atSpeak(text);
        });
        bubble.appendChild(document.createElement("br"));
        bubble.appendChild(soundBtn);
    }

    wrap.appendChild(bubble);
    return wrap;
}

function atSpeak(text) {
    if (!text || !window.speechSynthesis) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "th-TH";
    utterance.rate = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

function atSendCurrentInput() {
    const textarea = document.getElementById("atTextarea");
    const text = textarea.value.trim();
    if (!text) return;

    textarea.value = "";
    atSendMessage(text);
}

function atSendMessage(text) {
    if (atSending || !atCurrentMode) return;
    atSending = true;

    const history = atHistories[atCurrentMode];
    history.push({ role: "user", content: text });
    atRenderMessages();

    const box = document.getElementById("atMessages");
    const typing = document.createElement("div");
    typing.className = "at-typing";
    typing.id = "atTypingIndicator";
    typing.innerText = "AI Tutor กำลังพิมพ์...";
    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;

    const csrftoken = atGetCookie("csrftoken");
    const historyForRequest = history.slice(0, -1).map(function (item) {
        return { role: item.role, content: item.content };
    });

    fetch(window.AI_TUTOR_CHAT_URL, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            mode: atCurrentMode,
            message: text,
            history: JSON.stringify(historyForRequest),
        }),
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            const indicator = document.getElementById("atTypingIndicator");
            if (indicator) indicator.remove();

            if (result.data.ok) {
                history.push({ role: "assistant", content: result.data.reply });
            } else if (result.data.limit_reached) {
                history.push({
                    role: "assistant",
                    content: result.data.error,
                    isUpsell: true,
                });
            } else {
                history.push({
                    role: "assistant",
                    content: result.data.error || "เกิดข้อผิดพลาด กรุณาลองใหม่",
                    isError: true,
                });
            }
            atRenderMessages();
        })
        .catch(function () {
            const indicator = document.getElementById("atTypingIndicator");
            if (indicator) indicator.remove();

            history.push({
                role: "assistant",
                content: "เชื่อมต่อ AI ไม่ได้ กรุณาลองใหม่อีกครั้ง",
                isError: true,
            });
            atRenderMessages();
        })
        .finally(function () {
            atSending = false;
        });
}

function atToggleMic() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = document.getElementById("atMicBtn");

    if (!SpeechRecognition) {
        alert("เบราว์เซอร์นี้ยังไม่รองรับไมค์ แนะนำใช้ Google Chrome");
        return;
    }

    if (atRecognition) {
        atRecognition.stop();
        return;
    }

    atRecognition = new SpeechRecognition();
    atRecognition.lang = "th-TH";
    atRecognition.interimResults = false;
    atRecognition.continuous = false;

    micBtn.classList.add("recording");

    atRecognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        const textarea = document.getElementById("atTextarea");
        textarea.value = (textarea.value + " " + transcript).trim();
    };

    atRecognition.onerror = function () {
        micBtn.classList.remove("recording");
    };

    atRecognition.onend = function () {
        micBtn.classList.remove("recording");
        atRecognition = null;
    };

    atRecognition.start();
}

atInit();
