

let currentIndex = 0;
let score = 0;
let answeredTotal = 0;
let answered = false;

function shuffle(array) {
    return array.sort(() => Math.random() - 0.5);
}

function updateQuiz() {
    if (quizData.length === 0) return;

    answered = false;

    let quiz = quizData[currentIndex];

    document.getElementById("quizWord").innerText = quiz.word;
    document.getElementById("quizReading").innerText = quiz.reading;

    document.getElementById("quizCounter").innerText =
        (currentIndex + 1) + " / " + quizData.length;

    let progress = ((currentIndex + 1) / quizData.length) * 100;
    document.getElementById("quizProgress").style.width = progress + "%";

    let options = [quiz.correct];
    let shuffled = shuffle([...allMeanings]);

    for (let item of shuffled) {
        if (item !== quiz.correct && options.length < 4) {
            options.push(item);
        }
    }

    options = shuffle(options);

    let html = "";

    options.forEach(function(option) {
        html += `
            <button
                class="fern-option"
                onclick="checkAnswer(this, '${option.replace(/'/g, "\\'")}')"
            >
                ${option}
            </button>
        `;
    });

    document.getElementById("quizOptions").innerHTML = html;
    document.getElementById("quizResult").style.display = "none";
}

function checkAnswer(button, answer) {
    if (answered) return;

    answered = true;
    answeredTotal++;

    let correct = quizData[currentIndex].correct;
    let result = document.getElementById("quizResult");

    document.querySelectorAll(".fern-option").forEach(btn => {
        if (btn.innerText === correct) {
            btn.classList.add("correct");
        }
    });

    if (answer === correct) {
        button.classList.add("correct");
        result.className = "fern-result correct";
        result.innerText = "✅ ถูกต้อง!";
        score++;
    } else {
        button.classList.add("wrong");
        result.className = "fern-result wrong";
        result.innerText = "❌ ยังไม่ถูก คำตอบที่ถูกคือ: " + correct;
    }

    result.style.display = "block";

    let percent = Math.round((score / answeredTotal) * 100);

    document.getElementById("scoreCircle").innerText = percent + "%";
    document.getElementById("correctCount").innerText = score;
    document.getElementById("answeredCount").innerText = answeredTotal;

    let completeUrl = "";

    // {% if course_code %}
    // completeUrl = "/th/vocabulary/complete/{{ course_code }}/";
    // {% else %}
    // completeUrl = "/th/vocabulary/complete/";
    // {% endif %}

    document.getElementById("completeLessonBtn").href =
        completeUrl + "?score=" + percent;
}

function nextQuiz() {
    currentIndex = currentIndex < quizData.length - 1 ? currentIndex + 1 : 0;
    updateQuiz();
}

function prevQuiz() {
    currentIndex = currentIndex > 0 ? currentIndex - 1 : quizData.length - 1;
    updateQuiz();
}

updateQuiz();