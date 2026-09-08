from fastapi import FastAPI

app = FastAPI(
    title="Secure Content Portal API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Secure Content Portal API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }