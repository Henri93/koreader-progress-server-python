import os

# Set DynamoDB backend before importing app
os.environ.setdefault("DB_BACKEND", "dynamodb")

from mangum import Mangum
from main import app

# Configure root_path for API Gateway path prefix (/reader)
# This ensures FastAPI routes work correctly when accessed via /reader/...
app.root_path = "/reader"

# Mangum wraps the FastAPI ASGI app for Lambda
handler = Mangum(app, lifespan="off")
