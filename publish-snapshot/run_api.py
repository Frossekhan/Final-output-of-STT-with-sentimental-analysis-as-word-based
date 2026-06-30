import sys
from pathlib import Path

import uvicorn


if __name__ == "__main__":
    log_file = Path(__file__).with_name("uvicorn.combined.log").open("a", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    uvicorn.run("app:app", host="127.0.0.1", port=8000)
