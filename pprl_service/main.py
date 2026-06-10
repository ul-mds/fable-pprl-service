import uvicorn
from fastapi import FastAPI
from fable_model import HealthResponse

from pprl_service.config import Settings, Role
from pprl_service.routers import match, transform, mask


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/healthz", response_model=HealthResponse)
    async def get_health():
        return HealthResponse()

    role = Settings().role

    if role == Role.data_owner or role == Role.both:
        app.include_router(transform.router, prefix="/transform")
        app.include_router(mask.router, prefix="/mask")
    if role == Role.linkage_unit or role == Role.both:
        app.include_router(match.router, prefix="/match")

    print(app.routes)

    return app


def run_server():
    uvicorn.run(create_app())


if __name__ == "__main__":
    run_server()
