import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("ECHONODE_HOST", "0.0.0.0")
    port = int(os.getenv("ECHONODE_PORT", "8000"))
    print(f"Starting EchoNode Ingestion Hub on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
