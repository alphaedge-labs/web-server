from fastapi import FastAPI, Request
from fastapi.websockets import WebSocket, WebSocketDisconnect
from loguru import logger
from contextlib import asynccontextmanager
import logging
import sys
import asyncio

from app.services.websocket import manager
from app.config import (
    HOST,
    PORT
)
from app.services.realtime import RealtimeService

from app.routes.dashboard import router as dashboard_router
from app.routes.orders import router as orders_router
from app.routes.positions import router as positions_router

logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)
logger.add(
    "./app.log",  # File path for logging
    rotation="500 MB",  # Rotate when file reaches 500MB
    retention="10 days",  # Keep logs for 10 days
    compression="zip",  # Compress rotated logs
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)

# Intercept uvicorn's default logger
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Setup intercept handler for uvicorn
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create and start realtime service
    realtime_service = RealtimeService()
    asyncio.create_task(realtime_service.start_listening())
    yield
    # Stop realtime service
    await realtime_service.stop_listening()

app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(positions_router, prefix="/api/v1/positions", tags=["positions"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info(f'Running application on {HOST}:{PORT}')
    uvicorn.run(app, host=HOST, port=PORT)
