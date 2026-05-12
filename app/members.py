from functools import wraps

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from .auth import login_required
from .extensions import db
from .family_trees import can_access_family_tree
from .models import FamilyTree, Member


bp = Blueprint("members", __name__, url_prefix="/family-trees/<int:tree_id>/members")

GENDERS = {"male", "female", "unknown"}


def accessible_tree_required(view):
    @wraps(view)
    def wrapped_view(tree_id, **kwargs):
        family_tree = db.session.get(FamilyTree, tree_id)
        if family_tree is None:
            abort(404)
        if not can_access_family_tree(g.user, family_tree):
            abort(403)
        return view(family_tree, **kwargs)

    return wrapped_view


def get_member_or_404(family_tree, member_id):
    member = db.session.get(Member, member_id)
    if member is None or member.family_tree_id != family_tree.id:
        abort(404)
    return member


def parse_optional_int(value, field_label):
    value = value.strip()
    if not value:
        return None, None
    try:
        return int(value), None
    except ValueError:
        return None, f"{field_label} must be an integer."


def member_form_data():
    name = request.form.get("name", "").strip()
    gender = request.form.get("gender", "unknown").strip() or "unknown"
    biography = request.form.get("biography", "").strip()

    birth_year, error = parse_optional_int(request.form.get("birth_year", ""), "Birth year")
    if error:
        return None, error
    death_year, error = parse_optional_int(request.form.get("death_year", ""), "Death year")
    if error:
        return None, error
    generation, error = parse_optional_int(request.form.get("generation", ""), "Generation")
    if error:
        return None, error

    if not name:
        return None, "Name is required."
    if gender not in GENDERS:
        return None, "Gender is invalid."
    if generation is not None and generation <= 0:
        return None, "Generation must be greater than 0."
    if birth_year is not None and death_year is not None and death_year < birth_year:
        return None, "Death year must be greater than or equal to birth year."

    return {
        "name": name,
        "gender": gender,
        "birth_year": birth_year,
        "death_year": death_year,
        "generation": generation,
        "biography": biography,
    }, None


@bp.get("")
@login_required
@accessible_tree_required
def index(family_tree):
    query = request.args.get("q", "").strip()
    members_query = Member.query.filter_by(family_tree_id=family_tree.id)
    if query:
        members_query = members_query.filter(Member.name.ilike(f"%{query}%"))
    members = members_query.order_by(Member.id).all()
    return render_template(
        "members/index.html",
        family_tree=family_tree,
        members=members,
        query=query,
    )


@bp.route("/new", methods=("GET", "POST"))
@login_required
@accessible_tree_required
def create(family_tree):
    if request.method == "POST":
        data, error = member_form_data()
        if error:
            return render_template("members/new.html", family_tree=family_tree, error=error), 400

        member = Member(family_tree_id=family_tree.id, **data)
        db.session.add(member)
        db.session.commit()
        return redirect(
            url_for("members.detail", tree_id=family_tree.id, member_id=member.id)
        )

    return render_template("members/new.html", family_tree=family_tree, error=None)


@bp.get("/<int:member_id>")
@login_required
@accessible_tree_required
def detail(family_tree, member_id):
    member = get_member_or_404(family_tree, member_id)
    return render_template("members/detail.html", family_tree=family_tree, member=member)


@bp.route("/<int:member_id>/edit", methods=("GET", "POST"))
@login_required
@accessible_tree_required
def edit(family_tree, member_id):
    member = get_member_or_404(family_tree, member_id)

    if request.method == "POST":
        data, error = member_form_data()
        if error:
            return render_template(
                "members/edit.html",
                family_tree=family_tree,
                member=member,
                error=error,
            ), 400

        for field, value in data.items():
            setattr(member, field, value)
        db.session.commit()
        return redirect(
            url_for("members.detail", tree_id=family_tree.id, member_id=member.id)
        )

    return render_template(
        "members/edit.html",
        family_tree=family_tree,
        member=member,
        error=None,
    )


@bp.post("/<int:member_id>/delete")
@login_required
@accessible_tree_required
def delete(family_tree, member_id):
    member = get_member_or_404(family_tree, member_id)
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for("members.index", tree_id=family_tree.id))
