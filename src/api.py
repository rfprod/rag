from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

import app as rag_module


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_module.initialize()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root(question: str | None = None):
    if question:
        answer = rag_module.rag_application.run(question)
        return {"question": question, "answer": answer}
    return {
        "message": "RAG application is online. Pass a `question` as a query parameter to this endpoint."
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
