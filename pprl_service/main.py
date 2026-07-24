import uvicorn
from fastapi import FastAPI
from fable_model import HealthResponse

from pprl_service.config import Settings, Role
from pprl_service.routers import match, transform, mask


def create_app() -> FastAPI:
    s = Settings()

    app = FastAPI(
        title="FABLE PPRL Service",
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

    @app.get("/healthz", response_model=HealthResponse)
    async def get_health():
        return HealthResponse()

    if s.role == Role.data_owner or s.role == Role.both:
        app.include_router(transform.router, prefix="/transform")
        app.include_router(mask.router, prefix="/mask")
    if s.role == Role.linkage_unit or s.role == Role.both:
        app.include_router(match.router, prefix="/match")

    print(app.routes)

    return app


def run_server():
    uvicorn.run(create_app())


if __name__ == "__main__":
    run_server()
