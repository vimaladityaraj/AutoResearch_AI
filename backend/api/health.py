from fastapi import APIRouter
from backend.core.config import get_settings
from backend.models.schemas import HealthResponse
router = APIRouter(prefix='/health', tags=['health'])
@router.get('/', response_model=HealthResponse)
def health():
    cfg = get_settings()
    return HealthResponse(status='ok', provider=cfg.llm_provider, model=cfg.ollama_model)
