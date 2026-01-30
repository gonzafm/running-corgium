import os

# Mock environment variables for testing
# These must be set before src.config is imported
os.environ["STRAVA_CLIENT_ID"] = "12345"
os.environ["STRAVA_CLIENT_SECRET"] = "mock_secret"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret"
