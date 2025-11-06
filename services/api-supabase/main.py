from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import supabase
from routes.orders import router as orders_router

app = FastAPI(title="Supabase Web API",
              root_path="/api/supabase" )

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (each router can have its own prefix)
app.include_router(orders_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Ready Supabase"}