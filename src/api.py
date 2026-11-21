import asyncio

from typing import Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI, responses, HTTPException, staticfiles
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn

import app as rag_module

import skills as skills_module
import mcp_server as mcp_server_module
import configuration as configuration_module

semaphore = asyncio.Semaphore(configuration_module.MAX_CONCURRENCY)

mcp_service: Optional[mcp_server_module.RAGApplicationMCP] = None
_mcp_async_server_gateway_interface: Optional[ASGIApp] = None


async def mcp_async_server_gateway_interface(
    scope: Scope, receive: Receive, send: Send
):
    """Serve as the ASGI entry point for the ``/mcp`` route.

    This coroutine implements the ASGI application interface and delegates
    each request to the MCP ASGI app that is created during the application's
    lifespan startup. If that app does not exist yet, the request receives a
    **503 Service Unavailable** plain-text response instead.

    Args:
        scope: The ASGI connection scope dictionary describing the incoming
            connection, including its type, path, method, and headers.
        receive: An awaitable callable that returns ASGI event messages from
            the client, such as request body chunks or disconnect events.
        send: An awaitable callable used to emit ASGI event messages to the
            client, such as the response start and response body messages.

    Returns:
        None. The response is written to the client through ``send``.

    Raises:
        Any exception raised by the underlying MCP application propagates to
        the caller, which is typically the ASGI server. This function does not
        catch or translate those exceptions.

    Note:
        ``_mcp_async_server_gateway_interface`` is a module-level variable that
        is assigned during lifespan startup. If the lifespan has not completed,
        for example because the server is still starting or the lifespan
        protocol was not run, this function returns a 503 response with the
        body ``"MCP server is not ready."`` and does not forward the request.
    """
    if _mcp_async_server_gateway_interface is None:
        await PlainTextResponse("MCP server is not ready.", status_code=503)(
            scope, receive, send
        )
        return
    await _mcp_async_server_gateway_interface(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage startup and shutdown of the RAG and MCP components.

    On startup, this initializes the RAG module, creates the MCP service
    wrapping the RAG application, and builds the ASGI app that serves the
    ``/mcp`` route. The ASGI app is stored in the module-level variable
    ``_mcp_async_server_gateway_interface``, which
    ``mcp_async_server_gateway_interface`` forwards requests to. Until this
    startup sequence completes, that variable remains ``None`` and incoming
    ``/mcp`` requests receive a 503 response.

    The MCP session manager is kept running for the entire time the
    application is serving requests. It is shut down automatically when the
    ``async with`` block exits, which happens after the application stops
    accepting new requests.

    Args:
        app: The FastAPI application this lifespan is attached to. It is
            required by the FastAPI lifespan protocol but is not used directly.

    Yields:
        None. Control returns to FastAPI to serve requests while the
        application is running.

    Raises:
        Any exception raised by ``rag_module.initialize()`` or during MCP
        setup prevents the application from starting, because the exception
        is raised before the ``yield``.

    Side Effects:
        Assigns the global variables ``mcp_service`` and
        ``_mcp_async_server_gateway_interface``. These are not reset during
        shutdown.
    """
    global mcp_service, _mcp_async_server_gateway_interface

    rag_module.initialize()

    mcp_service = mcp_server_module.RAGApplicationMCP(
        rag_module.rag_application, semaphore
    )
    mcp = mcp_service.get_mcp()
    _mcp_async_server_gateway_interface = mcp.streamable_http_app(
        streamable_http_path="/", stateless_http=True
    )

    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")

app.mount("/mcp", mcp_async_server_gateway_interface)


@app.get("/")
async def root(question: str | None = None, skill: str | None = None):
    """Answer a question with the RAG application, or describe how to use the endpoint.

    If no usable ``question`` is supplied, this returns a message explaining
    how to call the endpoint. Otherwise, the question is passed to the RAG
    application and the generated answer is returned. Concurrent requests are
    limited by ``semaphore``. A request waits up to
    ``configuration_module.TIMEOUT`` seconds for a free slot before it is
    rejected.

    Args:
        question: The question to answer. Leading and trailing whitespace is
            removed. ``None``, an empty string, or a whitespace-only string
            returns the usage message instead of an answer.
        skill: An optional skill name used to narrow the search. It is passed
            unchanged to the RAG application.

    Returns:
        dict: ``{"message": str}`` when no usable question is provided.
        Otherwise, ``{"question": str, "answer": str}``, where ``question`` is
        the stripped question text.

    Raises:
        HTTPException: With status 503 in three cases. The RAG application has
            not been initialized. No concurrency slot became available within
            the timeout, in which case a ``Retry-after`` header is included.
            The RAG application raised a ``ValueError``, in which case the
            error message is returned as the detail.
    """

    quest: str = "" if question is None else question.strip()
    if not quest:
        return {
            "message": "RAG application is online. Pass a non-empty `question` as a query parameter to this endpoint. This endpoint also supports a `skill` as a query parameter to narrow down search."
        }

    if rag_module.rag_application is None:
        raise HTTPException(
            status_code=503,
            detail=f"Something went wrong. It is possible tha the `rag_module` was not initialized. `rag_module.rag_application` is `None`.",
        )

    try:
        await asyncio.wait_for(
            semaphore.acquire(), timeout=configuration_module.TIMEOUT
        )
    except TimeoutError:
        raise HTTPException(
            status_code=503,
            detail=f"Concurrent request capacity reached. Maximum concurrency: {configuration_module.MAX_CONCURRENCY}.",
            headers={"Retry-after": f"{configuration_module.TIMEOUT}"},
        )

    answer: str = ""

    try:
        answer = await asyncio.to_thread(rag_module.rag_application.run, quest, skill)
    except ValueError as err:
        raise HTTPException(
            status_code=503,
            detail=f"{err}",
        )
    finally:
        semaphore.release()

    return {"question": quest, "answer": answer}


@app.get("/skills")
async def skills():
    """List the skill URLs that the RAG application can use.

    Returns:
        A JSON array containing the values of ``skills_module.skill_urls``.
        The values are returned, not the keys.
    """

    skills: list[str] = []
    for _, skill in skills_module.skill_urls.items():
        skills.append(skill)

    return responses.JSONResponse(skills)


@app.get("/tools", response_model=list[str])
async def tools():
    """List the names of the tools exposed by the MCP server.

    Returns:
        list[str]: The tool names, in the order reported by the MCP server.

    Raises:
        HTTPException: With status 503 if the MCP service has not been created
            yet, for example because application startup has not finished.
    """

    if mcp_service is None:
        raise HTTPException(status_code=503, detail="MCP server is not initialized.")
    tool_list = await mcp_service.get_mcp().list_tools()
    return [tool.name for tool in tool_list]


@app.get("/ui")
async def ui():
    """Serve the browser-based user interface.

    Returns:
        FileResponse: The contents of ``static/index.html``.

    Note:
        The path is relative to the current working directory, so the server
        must be started from the directory that contains ``static/``. If the
        file is missing, the error occurs when the response is sent, not when
        this function runs.
    """

    return responses.FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
