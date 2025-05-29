from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from runner import get_solidity_output

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

class PromptInput(BaseModel):
    prompt: str

@app.post("/generate")
def generate_code(data: PromptInput):
    code, explanation = get_solidity_output(data.prompt)
    return {
        "solidity_code": code,
        "explanation": explanation
    }
