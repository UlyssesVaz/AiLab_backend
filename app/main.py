from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

from .routes import upload


app = FastAPI(title="AI Virtual Lab API", version="1.0.0")

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])

@app.get("/")
async def root():
    return {"message": "AI Virtual Lab API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_configured": bool(os.getenv("OPENAI_API_KEY"))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)