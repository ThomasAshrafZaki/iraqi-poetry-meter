from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.meter import analyze_poem_line, list_weights

app = FastAPI(title="Iraqi Poetry Meter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API routes FIRST
@app.get("/api/weights")
def api_weights():
    return {"ok": True, "weights": list_weights()}


@app.post("/api/analyze")
async def api_analyze(payload: dict):
    text = (payload.get("text") or "").strip()
    if not text:
        return {
            "ok": False,
            "error": "empty_input",
            "message": "اكتب بيت/شطر واحد على الأقل."
        }

    return analyze_poem_line(text)


# ✅ Static mount LAST (IMPORTANT)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
