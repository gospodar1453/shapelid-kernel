"""
AWS Lambda Handler — Mangum ile FastAPI'yi Lambda'ya bağlar.
Lambda event → ASGI → FastAPI → response
"""
from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
