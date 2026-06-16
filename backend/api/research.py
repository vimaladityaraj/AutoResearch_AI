from fastapi import APIRouter, HTTPException
from loguru import logger
from backend.models.schemas import ResearchRequest, ResearchReport
from backend.services.research_agent import ResearchAgent
router = APIRouter(prefix='/research', tags=['research'])
@router.post('/', response_model=ResearchReport)
def research(req: ResearchRequest):
    try:
        return ResearchAgent().run(req.company_name, req.industry_hint, req.focus_area, req.sources)
    except Exception as e:
        logger.exception('Research failed')
        raise HTTPException(status_code=500, detail=str(e))
