"""uvicorn entry: PYTHONPATH=src python run_server.py"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    src = Path(__file__).resolve().parent
    sys.path.insert(0, str(src))
    import uvicorn

    uvicorn.run("q2_audit.main:app", host="0.0.0.0", port=8000, reload=True)
