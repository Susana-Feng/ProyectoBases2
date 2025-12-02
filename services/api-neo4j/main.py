import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_neo4j_driver
from routes.orders import router as orders_router
from routes.clients import router as clients_router
from routes.products import router as products_router

app = FastAPI(title="Neo4j Web API", root_path="/api/neo4j")

DEFAULT_PORT = 3003

logging.basicConfig(level=os.getenv("NEO4J_LOG_LEVEL", "INFO"))

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (each router can have its own prefix)
app.include_router(orders_router)
app.include_router(clients_router)
app.include_router(products_router)


@app.on_event("startup")
async def startup_event():
    # initialize and store neo4j driver for reuse
    app.state.neo4j_driver = get_neo4j_driver()
    app.state.neo4j_driver.verify_connectivity()
    print("Connection established.")


@app.on_event("shutdown")
async def shutdown_event():
    driver = getattr(app.state, "neo4j_driver", None)
    if driver:
        try:
            driver.close()
        except Exception:
            pass


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Ready Neo4j"}


def run_dev():
    import uvicorn

    port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    run_dev()
