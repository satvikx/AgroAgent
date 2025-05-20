import sys
import os
import logging
from datetime import datetime

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Create logs directory if it doesn't exist
os.makedirs("fastapi_server/logs", exist_ok=True)

# Custom handler that ensures immediate flushing
class ImmediateFlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Get log level from environment variable or use INFO as default
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # This handler ensures logs go to stdout for Render to capture
        ImmediateFlushingStreamHandler(sys.stdout),
        # Keep file handler for local development and debugging
        logging.FileHandler(os.path.join("fastapi_server/logs", f"server_{datetime.now().strftime('%Y%m%d')}.log"), mode="a"),
    ]
)
logger = logging.getLogger("bagro_chatbot")

# Force flush at startup
print("=" * 50)
print("BAGRO CHATBOT SERVER INITIALIZING")
print("=" * 50)
sys.stdout.flush()
logger.info("Logging system initialized")