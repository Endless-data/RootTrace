from functools import wraps

from flask import (
    Blueprint,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import User


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id is not None else None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")

        if not username:
            error = "Username is required."
        elif not display_name:
            error = "Display name is required."
        elif not password:
            error = "Password is required."
        elif User.query.filter_by(username=username).first() is not None:
            error = "Username is already registered."

        if error is None:
            user = User(
                username=username,
                display_name=display_name,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("auth.login"))

        return render_template("auth/register.html", error=error), 400

    return render_template("auth/register.html", error=error)


@bp.route("/login", methods=("GET", "POST"))
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password_hash, password):
            error = "Invalid username or password."
        else:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("main.index"))

        return render_template("auth/login.html", error=error), 401

    return render_template("auth/login.html", error=error)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
