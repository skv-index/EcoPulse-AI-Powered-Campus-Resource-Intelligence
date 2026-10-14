"""Entry point:  py app.py   (also `py run.py`). Serves on PORT (default 5001)."""
from dotenv import load_dotenv

load_dotenv()  # read local .env before config is imported

from app import create_app
from app import config

app = create_app()

if __name__ == "__main__":
    print(f"EcoPulse resource-service on http://127.0.0.1:{config.PORT}")
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
