import uvicorn

import main
import settings

main_app = main.App

if __name__ == "__main__":
    uvicorn.run(
        "run:main_app",
        debug=settings.Settings.DEBUG,
        host=settings.Settings.HOST,
        port=settings.Settings.PORT,
        reload=settings.Settings.RELOAD,
        use_colors=settings.Settings.COLOR_LOGS,
        log_level=settings.Settings.LOGGER_LEVEL,
        proxy_headers=True,
    )
