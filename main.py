"""Minimal FastAPI app with JSON logs, request IDs, and Prometheus metrics."""

import json
import logging
import time
import uuid
from typing import List

from fastapi import FastAPI, Request, status
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("app")


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Latency per HTTP request",
    ["method", "path", "status"],
)


def _request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or uuid.uuid4().hex


class ItemIn(BaseModel):
    name: str


class ItemOut(ItemIn):
    id: int


class InMemoryStore:
    def __init__(self) -> None:
        self._items: List[ItemOut] = []
        self._next_id = 1

    def list_items(self) -> List[ItemOut]:
        return self._items

    def add_item(self, name: str) -> ItemOut:
        item = ItemOut(id=self._next_id, name=name)
        self._items.append(item)
        self._next_id += 1
        return item


store = InMemoryStore()
app = FastAPI(title="DevOps Demo API", version="1.0.0")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = _request_id(request)
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        latency = time.perf_counter() - start
        labels = {
            "method": request.method,
            "path": request.url.path,
            "status": str(response.status_code),
        }
        REQUEST_COUNT.labels(**labels).inc()
        REQUEST_LATENCY.labels(**labels).observe(latency)

        response.headers["x-request-id"] = request_id
        log = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(latency * 1000, 3),
        }
        logger.info(json.dumps(log))
        return response


app.add_middleware(RequestContextMiddleware)


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "request_id": request.state.request_id})


@app.get("/items")
async def list_items(request: Request) -> JSONResponse:
    items = [item.model_dump() for item in store.list_items()]
    payload = {"items": items, "count": len(items), "request_id": request.state.request_id}
    return JSONResponse(payload)


@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemIn, request: Request) -> JSONResponse:
    item = store.add_item(payload.name)
    return JSONResponse(
        {"item": item.model_dump(), "request_id": request.state.request_id},
        status_code=status.HTTP_201_CREATED,
    )


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root(request: Request) -> JSONResponse:
    return JSONResponse({"message": "DevOps demo API", "request_id": request.state.request_id})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)