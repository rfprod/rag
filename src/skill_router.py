import re

from langchain_ollama import ChatOllama

import configuration as configuration_module

ROUTER_PROMPT = """Choose the single skill that best matches the user's question.

Available skills: {skills}

Question: {question}

Reply with only the exact skill name from the list. If no skill clearly fits, reply NONE."""


class SkillRouter:
    """Selects the most relevant skill for a question using a small local LLM.

    The router sends the question and the list of valid skills to the model and
    accepts only an answer that matches one of those skills. Any other reply
    results in ``None``, which tells the retrieval layer to use the default retriever.

    Attributes:
        skills: The valid skill names, in their original case.
        llm: The chat model used for routing, with thinking disabled.
    """

    def __init__(
        self, skills: list[str], model: str = configuration_module.OLLAMA_ROUTING_MODEL
    ) -> None:
        """Initialize the router.

        Args:
            skills: Skill names that questions can be routed to.
            model: The Ollama model tag used for routing. Defaults to ``qwen3:1.7b``.
        """

        self.skills = list(skills)
        self._lookup = {name.lower(): name for name in self.skills}
        self.llm = ChatOllama(
            model=model,
            temperature=0,
            reasoning=False,  # Disable Qwen3's reasoning output for a fast, direct answer.
            num_predict=16,  # A skill name is short, so cap the output length.
        )

    def route(self, question: str) -> str | None:
        """Choose a skill for the question.

        Args:
            question: The user's question.

        Returns:
            The matching skill name, or ``None`` if no skill fits or the reply
            is not a known skill.
        """

        if not self.skills:
            return None

        prompt = ROUTER_PROMPT.format(skills=", ".join(self.skills), question=question)
        raw = str(self.llm.invoke(prompt).content)

        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
        answer = cleaned.strip().strip("\"'`.").lower()

        return self._lookup.get(answer)
