import os

from flask import Flask

from .extensions import db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
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

    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    from .family_trees import bp as family_trees_bp

    app.register_blueprint(family_trees_bp)

    from .members import bp as members_bp

    app.register_blueprint(members_bp)

    from .relationships import bp as relationships_bp

    app.register_blueprint(relationships_bp)

    return app
