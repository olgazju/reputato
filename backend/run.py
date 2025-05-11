"""
Entry point script with explicit path addition.
Place this in your backend directory.
"""
import sys
import os
import uvicorn

# Add the parent directory to path so Python can find your modules
#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)