"""Entry point: `python run.py` starts the AI service on PORT (default 5002)."""

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.config import PORT  # noqa: E402

app = create_app()

if __name__ == "__main__":
    print(f"AI service listening on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
