from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .sql_agent import answer_question


app = FastAPI(
    title="StockLoom Agentic AI",
    description="AI assistant for StockLoom inventory management",
    version="1.0.0",
)


class AgentRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "service": "StockLoom Agentic AI",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/agent/ask")
async def ask_agent(request: AgentRequest):
    try:
        result = await answer_question(
            request.question
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )