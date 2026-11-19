import asyncio
from datetime import datetime
import os

from mcp.server.mcpserver import MCPServer

import app as rag_module
import skills as skills_module
import skill_router as skill_router_module
import configuration as configuration_module


class RAGApplicationMCP:
    """MCP server wrapper that exposes the RAG application as MCP tools.

    The server provides three tools for MCP clients:

    - ``ask_knowledge_base``: answer a question with a generated response.
    - ``search_documents``: return raw retrieved chunks without generation.
    - ``list_skills``: list the skills that have dedicated retrievers.

    Blocking RAG calls run in a worker thread and share a concurrency limit
    (``semaphore``) with the REST endpoint, so MCP traffic cannot exceed the
    limit the REST API enforces.

    Attributes:
        rag_application: The initialized RAG application that answers queries
            and provides retrievers.
        semaphore: The shared semaphore that limits concurrent RAG calls.
        mcp: The ``MCPServer`` instance that hosts the registered tools.
    """

    def __init__(
        self,
        rag_application: rag_module.RAGApplication | None,
        semaphore: asyncio.Semaphore,
    ):
        """Initialize the MCP server and register its tools.

        Args:
            rag_application: The initialized RAG application. Must not be None.
            semaphore: The semaphore shared with the REST endpoint. Each RAG
                call acquires it before running.

        Raises:
            RuntimeError: If ``rag_application`` is None, meaning the RAG
                application failed to initialize before the MCP server was
                created.
        """
        if rag_application is None:
            raise RuntimeError("MCP server error: RAG application is not initialized.")

        self.rag_application = rag_application
        self.semaphore = semaphore

        self.router = skill_router_module.SkillRouter(skills=self._skill_names())

        mcp = MCPServer("rag-app")
        self.mcp = mcp

        @mcp.tool()
        async def ask_knowledge_base(question: str, skill: str | None = None) -> str:
            """Answer a question using the knowledge base.

            Retrieves relevant documents and generates a concise answer. Use this
            when the user wants a direct answer rather than the source text.

            Args:
                question: The natural-language question to answer.
                skill: Optional skill name, as returned by ``list_skills``, used
                    to narrow the search to that skill's documents.

            Returns:
                The generated answer as plain text.
            """
            return await self._guarded(
                self.rag_application.run, question.strip(), skill
            )

        @mcp.tool()
        async def search_documents(query: str, skill: str | None = None) -> list[dict]:
            """Return the raw document chunks most relevant to the query.

            No answer is generated. Use this when you want to read the sources
            yourself. If no skill is given, the most relevant skill is chosen
            automatically from the query.

            Args:
                query: The search query.
                skill: Optional skill name, as returned by ``list_skills``, used
                    to narrow the search. If omitted, a skill is selected from the
                    query. If the skill has no dedicated retriever, the default
                    retriever is used.

            Returns:
                A list of dictionaries, one per chunk, each with the keys
                ``"content"`` (the chunk text) and ``"metadata"`` (the chunk's
                metadata as stored in the knowledge base).
            """
            query = query.strip()
            resolved = await self._resolve_skill(query, skill)
            docs = await self._guarded(self._retriever_for(resolved).invoke, query)
            return [{"content": d.page_content, "metadata": d.metadata} for d in docs]

        @mcp.tool()
        def list_skills() -> list[str]:
            """List the skill names that have dedicated retrievers in the knowledge base.

            Returns:
                The skill names that can be passed as the ``skill`` argument of
                ``ask_knowledge_base`` and ``search_documents``.
            """
            return self._skill_names()

        @mcp.tool()
        def current_time() -> str:
            """Return the current date and time of the server in ISO 8601 format.

            The value uses the server's local timezone, not the client's, and is
            truncated to whole seconds.

            Returns:
                The current local date and time, for example
                ``"2026-11-19T14:30:05"``.
            """
            return datetime.now().isoformat(timespec="seconds")

        @mcp.tool()
        def read_file(filename: str) -> str:
            """Read a text file from the ``mcp_files/`` folder by its file name.

            Only files directly inside or below ``mcp_files/`` can be read. Paths
            that resolve to a location outside that folder are rejected. Files are
            decoded as UTF-8.

            Args:
                filename: The path of the file relative to ``mcp_files/``, such as
                    ``"notes.txt"`` or ``"reports/2026.md"``.

            Returns:
                The full text content of the file. If the path resolves outside
                ``mcp_files/``, an error message is returned instead of the file
                contents.

            Raises:
                FileNotFoundError: If no file exists at the given path.
                IsADirectoryError: If the path refers to a directory.
                UnicodeDecodeError: If the file is not valid UTF-8 text.
            """
            base = os.path.abspath("mcp_files")
            path = os.path.abspath(os.path.join(base, filename))
            if not path.startswith(base + os.sep):
                return f"Error: access outside the {base} folder is not allowed."
            with open(path, encoding="utf-8") as f:
                return f.read()

    def _skill_names(self) -> list[str]:
        """Return the skill names that have dedicated retrievers.

        Returns:
            The keys of the skill URL mapping, in definition order.
        """
        return [skill for _, skill in skills_module.skill_urls.items()]

    async def _guarded(self, fn, *args):
        """Run a blocking RAG call under the shared concurrency limit.

        Acquires the semaphore, runs ``fn`` in a worker thread, and releases the
        semaphore when the call finishes, even if it raises.

        Args:
            fn: The blocking callable to run, such as a retriever's ``invoke``
                method or the RAG application's ``run`` method.
            *args: Positional arguments passed to ``fn``.

        Returns:
            The value returned by ``fn``.

        Raises:
            asyncio.TimeoutError: If the semaphore cannot be acquired within
                ``configuration_module.TIMEOUT`` seconds.
            Exception: Any exception raised by ``fn`` is propagated unchanged.
        """
        await asyncio.wait_for(
            self.semaphore.acquire(), timeout=configuration_module.TIMEOUT
        )
        try:
            return await asyncio.to_thread(fn, *args)
        finally:
            self.semaphore.release()

    def _retriever_for(self, skill: str | None):
        """Select the retriever for a skill, falling back to the default.

        Args:
            skill: The skill name, or None to use the default retriever.

        Returns:
            The retriever registered for ``skill``. If ``skill`` is None or has
            no dedicated retriever, the ``"default"`` retriever is returned.
        """
        retrievers = self.rag_application.scoped_retrievers
        return (
            retrievers[skill]
            if skill in retrievers
            else self.rag_application.default_retriever
        )

    async def _resolve_skill(self, question: str, skill: str | None) -> str | None:
        """Pick a skill for a question when the caller did not provide one.

        Args:
            question: The user's question or search query.
            skill: The skill the caller provided, or ``None`` to route automatically.

        Returns:
            The provided skill unchanged, the skill chosen by the router, or ``None``
            if the router found no match. ``None`` falls back to the default retriever.
        """
        if skill is not None:
            return skill
        return await self._guarded(asyncio.to_thread, self.router.route, question)

    async def ask_knowledge_base(self, question: str, skill: str | None = None) -> str:
        """Answer a question from the knowledge base.

        If ``skill`` is omitted, the question is routed to the most relevant skill
        before retrieval.

        Args:
            question: The question to answer.
            skill: Optional skill name. Use ``list_skills`` to see valid names.

        Returns:
            The generated answer.
        """
        resolved = await self._resolve_skill(question, skill)
        return await self._guarded(self.rag_application.run, question, resolved)

    def get_mcp(self) -> MCPServer:
        """Return the underlying MCP server instance.

        Returns:
            The ``MCPServer`` that hosts this application's tools, for example so
            it can be mounted in an ASGI app or run as a standalone server.
        """
        return self.mcp
