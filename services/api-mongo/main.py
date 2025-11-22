from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_mongo_client, get_mssql_connection

from routers.orders import router as orders_router
from routers.clients import router as clients_router
from routers.products import router as products_router

app = FastAPI(title="MongoDB Web API",
              root_path="/api/mongo")

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # initialize and store mongo client for reuse
    app.state.mongo_client = get_mongo_client()
    app.state.mssql_connection = get_mssql_connection()


@app.on_event("shutdown")
async def shutdown_event():
    client = getattr(app.state, "mongo_client", None)
    if client:
        try:
            client.close()
        except Exception:
            pass
    mssql_connection = getattr(app.state, "mssql_connection", None)
    if mssql_connection:
        try:
            mssql_connection.close()
        except Exception:
            pass


# Include routers (each router can have its own prefix)
app.include_router(orders_router)
app.include_router(clients_router)
app.include_router(products_router)

@app.get("/")
async def root():
    return {"message": "Ready MongoDB"}