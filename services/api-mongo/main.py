from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_mongo_client

from routers.orders import router as orders_router
from routers.clients import router as clientes_router
from routers.products import router as productos_router

app = FastAPI(title="MongoDB Web API")

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
app.include_router(clientes_router)
app.include_router(productos_router)

@app.get("/")
async def root():
    return {"message": "Ready MongoDB"}