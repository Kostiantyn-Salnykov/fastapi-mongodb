import uvicorn

from main import app
from settings import settings

main_app = app

if __name__ == "__main__":
    uvicorn.run(
        "run:main_app",
        debug=settings.DEBUG,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        use_colors=settings.COLOR_LOGS,
        log_level=settings.UVICORN_LOG_LEVEL,
        proxy_headers=True,
    )
