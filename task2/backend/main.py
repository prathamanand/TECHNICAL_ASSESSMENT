from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

# Enable frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    input: str

@app.post("/explain")
def explain_contract(data: InputData):
    try:
        result = subprocess.run(
            ["python", "explain_contract.py", data.input],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {"output": result.stdout}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Timeout while generating contract.")
