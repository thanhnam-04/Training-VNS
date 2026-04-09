import os

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://content-service:8002")

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def proxy_request(request: Request, target_base: str, path: str) -> Response:
    target_url = f"{target_base}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    async with httpx.AsyncClient(timeout=60.0) as client:
        upstream = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.query_params,
            content=await request.body(),
        )

    filtered_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in {"content-encoding", "transfer-encoding", "connection"}
    }
    return Response(content=upstream.content, status_code=upstream.status_code, headers=filtered_headers)


@app.api_route("/api/auth", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_auth_root(request: Request):
    return await proxy_request(request, AUTH_SERVICE_URL, "/api/auth")


@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_auth(request: Request, path: str):
    if path.startswith("internal/"):
        return Response(content="Not Found", status_code=404)
    return await proxy_request(request, AUTH_SERVICE_URL, f"/api/auth/{path}")


@app.api_route("/api/posts", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_posts_root(request: Request):
    return await proxy_request(request, CONTENT_SERVICE_URL, "/api/posts")


@app.api_route("/api/posts/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_posts(request: Request, path: str):
    return await proxy_request(request, CONTENT_SERVICE_URL, f"/api/posts/{path}")


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
