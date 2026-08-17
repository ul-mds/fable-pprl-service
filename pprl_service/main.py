import uvicorn
from fastapi import FastAPI
from fable_model import HealthResponse, ServiceBaseInformation

from pprl_service.config import Settings, Role
from pprl_service.routers import match, transform, mask
from pprl_service.version import __version__


def create_app() -> FastAPI:
    s = Settings()

    app = FastAPI(
        title="FABLE PPRL Service",
        version=__version__,
        openapi_tags=[
            {
                "name": "transform",
                "description": "Preprocess records by applying a variety of transformers.",
            },
            {
                "name": "mask",
                "description": "Mask records based on Bloom filter techniques.",
            },
            {
                "name": "match",
                "description": "Compute similarities between bit vector pairs and classify them.",
            },
        ],
        openapi_url="/openapi.json" if s.expose_docs else None,
        docs_url="/docs" if s.expose_docs else None,
        redoc_url="/redoc" if s.expose_docs else None,
    )

    @app.get("/", response_model=ServiceBaseInformation)
    async def get_info():
        return ServiceBaseInformation(version=__version__)

    @app.get("/healthz", response_model=HealthResponse)
    async def get_health():
        return HealthResponse()

    if s.role == Role.data_owner or s.role == Role.both:
        app.include_router(transform.router, prefix="/transform")
        app.include_router(mask.router, prefix="/mask")
    if s.role == Role.linkage_unit or s.role == Role.both:
        app.include_router(match.router, prefix="/match")

    return app


def run_server():
    uvicorn.run(create_app())


if __name__ == "__main__":
    run_server()
