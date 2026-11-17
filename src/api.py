import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI, responses, HTTPException, staticfiles
import uvicorn

import app as rag_module


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_module.initialize()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")

MAX_CONCURRENCY = 1
TIMEOUT = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)


@app.get("/")
async def root(question: str | None = None):
    quest = "" if question is None else question.strip()
    if not quest:
        return {
            "message": "RAG application is online. Pass a non-empty `question` as a query parameter to this endpoint."
        }

    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=TIMEOUT)
    except TimeoutError:
        raise HTTPException(
            status_code=503,
            detail=f"Concurrent request capacity reached. Maximum concurrency: {MAX_CONCURRENCY}.",
            headers={"Retry-after": f"{TIMEOUT}"},
        )

    answer = rag_module.rag_application.run(quest)
    return {"question": quest, "answer": answer}


@app.get("/ui")
async def ui():
    return responses.FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
