document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM content loaded');

  const form = document.getElementById("question-form");
  const questionInput = document.getElementById("question");
  const answerElement = document.getElementById("answer");
  const resultElement = document.getElementById("result");
  const errorElement = document.getElementById("error");
  const submitButton = form.querySelector("button");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
      return;
    }

    resultElement.hidden = true;
    errorElement.textContent = "";
    submitButton.disabled = true;
    submitButton.textContent = "Asking...";

    try {
      const response = await fetch(`/?question=${question}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = await response.json();

      answerElement.textContent = data.answer;
      resultElement.hidden = false;
    } catch (error) {
      errorElement.textContent =
        "Unable to get an answer. Please try again.";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Ask";
    }
  });
})
