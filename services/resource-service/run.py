"""Alt entry point:  py run.py"""
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app import config

app = create_app()

if __name__ == "__main__":
    print(f"EcoPulse resource-service on http://127.0.0.1:{config.PORT}")
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
