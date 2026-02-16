from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.engine.matcher import analyze_text

app = FastAPI(title="Iraqi Poetry Meter")

app.mount("/static", StaticFiles(directory="static"), name="static")

class AnalyzeReq(BaseModel):
    text: str

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/api/analyze")
def analyze(req: AnalyzeReq):
    return analyze_text(req.text)
