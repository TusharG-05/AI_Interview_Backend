from app.server import app

with open("routes_final.txt", "w", encoding="utf-8") as f:
    for route in app.routes:
        if hasattr(route, "path") and "video" in route.path:
            methods = getattr(route, "methods", ["WS"])
            f.write(f"DEBUG_ROUTE: {list(methods)} '{route.path}'\n")
        elif hasattr(route, "path") and "test" in route.path:
            f.write(f"DEBUG_ROUTE_TEST: {route.path}\n")
