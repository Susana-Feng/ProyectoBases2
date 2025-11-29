import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import supabase
from routes.orders import router as orders_router
from routes.clients import router as clients_router
from routes.products import router as products_router

app = FastAPI(title="Supabase Web API",
              root_path="/api/supabase" )

DEFAULT_PORT = 3004

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

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Ready Supabase"}


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