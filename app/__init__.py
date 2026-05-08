import os

from flask import Flask

from .extensions import db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://localhost/roottrace",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(bp)

    return app
