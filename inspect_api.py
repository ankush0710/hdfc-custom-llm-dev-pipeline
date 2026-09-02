import sys
import os
import json

sys.path.insert(0, os.path.abspath("backend"))

from app.main import app

def get_route_details():
    openapi_schema = app.openapi()
    with open("backend_openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print("OpenAPI schema dumped to backend_openapi.json successfully.")
    
    paths = openapi_schema.get("paths", {})
    print(f"Total paths in OpenAPI: {len(paths)}")
    for path, methods in paths.items():
        for method, details in methods.items():
            tags = details.get("tags", [])
            summary = details.get("summary", "")
            operationId = details.get("operationId", "")
            print(f"{method.upper():<7} {path:<60} {tags} {summary}")

if __name__ == "__main__":
    get_route_details()
