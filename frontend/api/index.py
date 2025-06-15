# Vercel Serverless Function for backend
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="InfuMatch API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "InfuMatch API is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "infumatch-backend"}

@app.get("/api/v1/influencers")
async def get_influencers():
    return {
        "success": True,
        "data": [],
        "message": "Influencers endpoint working"
    }

# Vercel用のハンドラー
def handler(request):
    return app