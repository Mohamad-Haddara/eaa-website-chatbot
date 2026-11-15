"""
Build the FastAPI app: routes, CORS, security headers, start-up and shut-down of the Azure Client

"""
from fastapi import FastAPI
import uvicorn
import asyncio

app = FastAPI(
    title="EAA website chatbot API",

)


@app.get("/health")
async def health() -> dict[str, str]:
    """ """
    return {
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
