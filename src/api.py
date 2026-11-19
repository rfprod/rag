import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI, responses, HTTPException, staticfiles
from starlette.responses import PlainTextResponse
import uvicorn

import app as rag_module

import skills as skills_module
import mcp_server as mcp_server_module
import configuration as configuration_module

semaphore = asyncio.Semaphore(configuration_module.MAX_CONCURRENCY)

mcp_service: mcp_server_module.RAGApplicationMCP | None = None
_mcp_asgi_app = None


async def mcp_asgi(scope, receive, send):
    """Forward /mcp requests to the MCP app once it has been created in the lifespan."""
    if _mcp_asgi_app is None:
        await PlainTextResponse("MCP server is not ready.", status_code=503)(
            scope, receive, send
        )
        return
    await _mcp_asgi_app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_service, _mcp_asgi_app

    rag_module.initialize()

    mcp_service = mcp_server_module.RAGApplicationMCP(
        rag_module.rag_application, semaphore
    )
    mcp = mcp_service.get_mcp()
    _mcp_asgi_app = mcp.streamable_http_app(
        streamable_http_path="/", stateless_http=True
    )

    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")

app.mount("/mcp", mcp_asgi)


@app.get("/")
async def root(question: str | None = None, skill: str | None = None):
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
    skills = []
    for _, skill in skills_module.skill_urls.items():
        skills.append(skill)

    return responses.JSONResponse(skills)


@app.get("/tools", response_model=list[str])
async def tools():
    if mcp_service is None:
        raise HTTPException(status_code=503, detail="MCP server is not initialized.")
    tool_list = await mcp_service.get_mcp().list_tools()
    return [tool.name for tool in tool_list]


@app.get("/ui")
async def ui():
    return responses.FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
