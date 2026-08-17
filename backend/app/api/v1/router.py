from fastapi import APIRouter
from app.api.v1 import health, analyze, search, war_room, contracts, drafts, cases, statutes, qa

router = APIRouter()

router.include_router(health.router,    tags=["Health"])
router.include_router(analyze.router,   prefix="/analyze",   tags=["Judgment Predictor"])
router.include_router(search.router,    prefix="/search",    tags=["Hybrid Search"])
router.include_router(war_room.router,  prefix="/war-room",  tags=["War Room"])
router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
router.include_router(drafts.router,    prefix="/drafts",    tags=["Drafting"])
router.include_router(cases.router,     prefix="/cases",     tags=["Cases"])
router.include_router(statutes.router,  prefix="/statutes",  tags=["Statutory Mapping"])
router.include_router(qa.router,        prefix="/qa",        tags=["RAG Q&A"])
