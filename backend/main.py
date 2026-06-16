from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.health import router as health_router
from backend.api.research import router as research_router

app = FastAPI(title='AutoResearch AI', description='Autonomous competitive intelligence agent', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(health_router)
app.include_router(research_router)
@app.get('/')
def root():
    return {'name': 'AutoResearch AI', 'status': 'running'}
