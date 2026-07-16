"""Built-in prompt templates for common AI tasks."""

from typing import Any

from app.ai.prompts.base import BasePrompt


class GeneralChatPrompt(BasePrompt):
    """General-purpose conversation prompt."""

    name = "general_chat"
    description = "General-purpose conversation"
    system_prompt = (
        "You are ForgeAI Assistant, a helpful AI assistant built into the "
        "ForgeAI Operations Platform. You are knowledgeable, concise, and "
        "helpful. You assist users with general questions, software "
        "engineering tasks, and AI operations workflows. When you are unsure "
        "about something, say so honestly."
    )

    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context and "history" in context:
            for msg in context["history"][-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})
        return messages


class CodeExplanationPrompt(BasePrompt):
    """Prompt for explaining code snippets."""

    name = "code_explanation"
    description = "Explain how a piece of code works"
    system_prompt = (
        "You are a senior software engineer. Explain the provided code "
        "clearly and thoroughly, covering what it does, how it works, key "
        "patterns used, and any potential issues or improvements."
    )

    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})
        return messages


class PlanningPrompt(BasePrompt):
    """Prompt for planning and task decomposition."""

    name = "planning"
    description = "Break down tasks into actionable steps"
    system_prompt = (
        "You are a technical planning assistant. Given a goal or task, "
        "break it down into clear, actionable steps. Consider dependencies, "
        "risks, and best practices. Present a structured plan with phases "
        "and milestones."
    )

    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})
        return messages


class SummarizationPrompt(BasePrompt):
    """Prompt for summarizing text."""

    name = "summarization"
    description = "Summarize long text or documents"
    system_prompt = (
        "You are a concise summarizer. Given text, provide a clear and "
        "accurate summary that captures the key points, main arguments, and "
        "conclusions. Preserve important details while reducing length."
    )

    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        messages.append({"role": "user", "content": user_input})
        return messages


class DocumentationPrompt(BasePrompt):
    """Prompt for generating documentation."""

    name = "documentation"
    description = "Generate or improve documentation"
    system_prompt = (
        "You are a technical documentation specialist. Given code, a "
        "feature description, or existing docs, generate clear, "
        "well-structured documentation including descriptions, usage "
        "examples, parameters, and return values as appropriate."
    )

    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context and "history" in context:
            for msg in context["history"][-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})
        return messages
