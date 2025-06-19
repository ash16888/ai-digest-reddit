"""AWS Lambda handler for FastAPI Reddit AI Digest application."""
from mangum import Mangum
from src.web_app import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")