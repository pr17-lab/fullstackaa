from fastapi import APIRouter

router = APIRouter()

# Placeholder for academic endpoints
# Will be implemented in development phase

@router.post("/terms")
async def create_term():
    return {"message": "Create term endpoint - To be implemented"}

@router.get("/terms")
async def get_terms():
    return {"message": "Get terms endpoint - To be implemented"}

@router.get("/analytics")
async def get_analytics():
    return {"message": "Get analytics endpoint - To be implemented"}
