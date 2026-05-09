from datetime import date
from functools import wraps

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from .auth import login_required
from .extensions import db
from .models import FamilyTree, FamilyTreeCollaborator, User


bp = Blueprint("family_trees", __name__, url_prefix="/family-trees")


def can_access_family_tree(user, family_tree):
    if user is None:
        return False
    if family_tree.created_by_user_id == user.id:
        return True
    return any(collaboration.user_id == user.id for collaboration in family_tree.collaborators)


def owner_required(view):
    @wraps(view)
    def wrapped_view(tree_id, **kwargs):
        family_tree = db.session.get(FamilyTree, tree_id)
        if family_tree is None:
            abort(404)
        if family_tree.created_by_user_id != g.user.id:
            abort(403)
        return view(family_tree, **kwargs)

    return wrapped_view


def parse_revision_time(raw_value):
    if not raw_value:
        return None
    return date.fromisoformat(raw_value)


@bp.get("")
@login_required
def index():
    created_trees = FamilyTree.query.filter_by(created_by_user_id=g.user.id).all()
    collaborated_trees = (
        FamilyTree.query.join(FamilyTreeCollaborator)
        .filter(FamilyTreeCollaborator.user_id == g.user.id)
        .all()
    )

    trees_by_id = {tree.id: tree for tree in created_trees}
    for tree in collaborated_trees:
        trees_by_id[tree.id] = tree

    return render_template(
        "family_trees/index.html",
        family_trees=list(trees_by_id.values()),
    )


@bp.route("/new", methods=("GET", "POST"))
@login_required
def create():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        revision_time_raw = request.form.get("revision_time", "").strip()

        if not name:
            error = "Family tree name is required."
        elif not surname:
            error = "Surname is required."

        if error is None:
            try:
                revision_time = parse_revision_time(revision_time_raw)
            except ValueError:
                return render_template("family_trees/new.html", error="Invalid revision date."), 400

            family_tree = FamilyTree(
                name=name,
                surname=surname,
                revision_time=revision_time,
                created_by_user_id=g.user.id,
            )
            db.session.add(family_tree)
            db.session.commit()
            return redirect(url_for("family_trees.detail", tree_id=family_tree.id))

        return render_template("family_trees/new.html", error=error), 400

    return render_template("family_trees/new.html", error=error)


@bp.get("/<int:tree_id>")
@login_required
def detail(tree_id):
    family_tree = db.session.get(FamilyTree, tree_id)
    if family_tree is None:
        abort(404)
    if not can_access_family_tree(g.user, family_tree):
        abort(403)
    return render_template("family_trees/detail.html", family_tree=family_tree)


@bp.post("/<int:tree_id>/collaborators")
@login_required
@owner_required
def add_collaborator(family_tree):
    username = request.form.get("username", "").strip()
    user = User.query.filter_by(username=username).first()

    if user is None:
        return render_template(
            "family_trees/detail.html",
            family_tree=family_tree,
            error="User does not exist.",
        ), 400
    if user.id == family_tree.created_by_user_id:
        return render_template(
            "family_trees/detail.html",
            family_tree=family_tree,
            error="Creator cannot be invited.",
        ), 400
    if any(collaboration.user_id == user.id for collaboration in family_tree.collaborators):
        return render_template(
            "family_trees/detail.html",
            family_tree=family_tree,
            error="User is already a collaborator.",
        ), 400

    db.session.add(
        FamilyTreeCollaborator(
            family_tree_id=family_tree.id,
            user_id=user.id,
            role="editor",
        )
    )
    db.session.commit()
    return redirect(url_for("family_trees.detail", tree_id=family_tree.id))
