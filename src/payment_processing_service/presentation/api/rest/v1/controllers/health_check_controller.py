from fastapi import APIRouter

router = APIRouter(prefix="/v1/healthcheck", tags=["Health check"])


@router.get("", response_model=dict)
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy"}
