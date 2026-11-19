document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById("question-form");
  const questionInput = document.getElementById("question");
  const skillSelect = document.getElementById("skill");
  const answerElement = document.getElementById("answer");
  const resultElement = document.getElementById("result");
  const errorElement = document.getElementById("error");
  const submitButton = form.querySelector("button");

  async function loadSkills() {
    try {
      const response = await fetch("/skills", {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to load skills: ${response.status}`);
      }

      const skills = await response.json();

      for (const skill of skills) {
        const option = document.createElement("option");
        option.value = skill;
        option.textContent = skill;
        skillSelect.append(option);
      }
    } catch (error) {
      console.error(error);
    }
  }

  await loadSkills();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
      return;
    }

    const params = new URLSearchParams({
      question,
      skill: skillSelect.value,
    });

    resultElement.hidden = true;
    errorElement.textContent = "";
    submitButton.disabled = true;
    submitButton.textContent = "Asking...";

    try {
      const response = await fetch(`/?${params.toString()}`, {
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
});
