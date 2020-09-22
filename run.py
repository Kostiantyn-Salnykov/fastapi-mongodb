import uvicorn

from main import app
from settings import settings

main_app = app

if __name__ == "__main__":
    uvicorn.run(
        "run:main_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        use_colors=settings.COLOR_LOGS,
        proxy_headers=True,
    )
