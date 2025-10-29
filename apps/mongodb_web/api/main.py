from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_mongo_client

from routers.orders import router as orders_router


app = FastAPI(title="MongoDB Web API")

# CORS — adjust origins for your frontend in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # initialize and store mongo client for reuse
    app.state.mongo_client = get_mongo_client()


@app.on_event("shutdown")
async def shutdown_event():
    client = getattr(app.state, "mongo_client", None)
    if client:
        try:
            client.close()
        except Exception:
            pass


# Include routers (each router can have its own prefix)
app.include_router(orders_router)


@app.get("/")
async def root():
    return {"message": "Ready MongoDB"}