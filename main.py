from api.app import create_app
from core.config import AppConfig, load_config
from core.engine import DetectionEngine


def build_app(config: AppConfig | None = None):
    app_config = config or load_config()
    engine = DetectionEngine(app_config)
    engine.start()

    app = create_app(engine, app_config)

    @app.teardown_appcontext
    def _shutdown(_exception=None):
        return None

    return app, engine, app_config


def main():
    app, engine, config = build_app()
    try:
        app.run(host=config.host, port=config.port, debug=False, use_reloader=False)
    finally:
        engine.stop()


if __name__ == "__main__":
    main()

