from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_neo4j_driver
from routes.orders import router as orders_router

app = FastAPI(title="Neo4j Web API",
              root_path="/api/neo4j" )

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (each router can have its own prefix)
app.include_router(orders_router)

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