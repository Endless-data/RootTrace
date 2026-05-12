from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, url_for

from .auth import login_required
from .extensions import db
from .members import accessible_tree_required, get_member_or_404, parse_optional_int
from .models import Marriage, Member, ParentChildRelationship


bp = Blueprint(
    "relationships",
    __name__,
    url_prefix="/family-trees/<int:tree_id>",
)

RELATIONSHIP_TYPES = {"father", "mother"}


def get_related_member(form_key, family_tree):
    raw_member_id = request.form.get(form_key, "").strip()
    member_id, error = parse_optional_int(raw_member_id, "Member ID")
    if error or member_id is None:
        return None, "Member ID must be an integer."
    member = db.session.get(Member, member_id)
    if member is None or member.family_tree_id != family_tree.id:
        return None, "Member must belong to this family tree."
    return member, None


def get_relationship_or_404(model, family_tree, relationship_id):
    relationship = db.session.get(model, relationship_id)
    if relationship is None or relationship.family_tree_id != family_tree.id:
        abort(404)
    return relationship


def relationship_tree_required(view):
    @wraps(view)
    @login_required
    @accessible_tree_required
    def wrapped_view(family_tree, **kwargs):
        return view(family_tree, **kwargs)

    return wrapped_view


def validate_parent_child(parent, child, relationship_type):
    if relationship_type not in RELATIONSHIP_TYPES:
        return "Relationship type is invalid."
    if parent.id == child.id:
        return "A member cannot be their own parent."
    if parent.birth_year is not None and child.birth_year is not None:
        if parent.birth_year >= child.birth_year:
            return "Parent birth year must be earlier than child birth year."
    duplicate = ParentChildRelationship.query.filter_by(
        parent_id=parent.id,
        child_id=child.id,
        relationship_type=relationship_type,
    ).first()
    if duplicate is not None:
        return "Parent-child relationship already exists."
    existing_same_type = ParentChildRelationship.query.filter_by(
        child_id=child.id,
        relationship_type=relationship_type,
    ).first()
    if existing_same_type is not None:
        return f"Child already has a {relationship_type}."
    return None


def normalized_marriage_pair(person_a, person_b):
    return tuple(sorted((person_a.id, person_b.id)))


def validate_marriage(person_a, person_b, start_year, end_year):
    if person_a.id == person_b.id:
        return "A member cannot marry themselves."
    if start_year is not None and end_year is not None and end_year < start_year:
        return "Marriage end year must be greater than or equal to start year."

    low_id, high_id = normalized_marriage_pair(person_a, person_b)
    duplicate = Marriage.query.filter(
        db.func.min(Marriage.person_a_id, Marriage.person_b_id) == low_id,
        db.func.max(Marriage.person_a_id, Marriage.person_b_id) == high_id,
    ).first()
    if duplicate is not None:
        return "Marriage relationship already exists."
    return None


def spouse_for(marriage, member):
    return marriage.person_b if marriage.person_a_id == member.id else marriage.person_a


@bp.get("/members/<int:member_id>/relationships")
@relationship_tree_required
def detail(family_tree, member_id):
    member = get_member_or_404(family_tree, member_id)
    marriages = (
        Marriage.query.filter_by(family_tree_id=family_tree.id, person_a_id=member.id).all()
        + Marriage.query.filter_by(family_tree_id=family_tree.id, person_b_id=member.id).all()
    )
    return render_template(
        "relationships/detail.html",
        family_tree=family_tree,
        member=member,
        marriages=marriages,
        spouse_for=spouse_for,
        error=None,
    )


@bp.post("/members/<int:member_id>/relationships/parents")
@relationship_tree_required
def add_parent(family_tree, member_id):
    child = get_member_or_404(family_tree, member_id)
    parent, error = get_related_member("parent_id", family_tree)
    relationship_type = request.form.get("relationship_type", "").strip()
    if error is None:
        error = validate_parent_child(parent, child, relationship_type)
    if error:
        return render_relationship_error(family_tree, child, error), 400

    db.session.add(
        ParentChildRelationship(
            family_tree_id=family_tree.id,
            parent_id=parent.id,
            child_id=child.id,
            relationship_type=relationship_type,
        )
    )
    db.session.commit()
    return redirect(
        url_for("relationships.detail", tree_id=family_tree.id, member_id=child.id)
    )


@bp.post("/members/<int:member_id>/relationships/children")
@relationship_tree_required
def add_child(family_tree, member_id):
    parent = get_member_or_404(family_tree, member_id)
    child, error = get_related_member("child_id", family_tree)
    relationship_type = request.form.get("relationship_type", "").strip()
    if error is None:
        error = validate_parent_child(parent, child, relationship_type)
    if error:
        return render_relationship_error(family_tree, parent, error), 400

    db.session.add(
        ParentChildRelationship(
            family_tree_id=family_tree.id,
            parent_id=parent.id,
            child_id=child.id,
            relationship_type=relationship_type,
        )
    )
    db.session.commit()
    return redirect(
        url_for("relationships.detail", tree_id=family_tree.id, member_id=parent.id)
    )


@bp.post("/members/<int:member_id>/relationships/marriages")
@relationship_tree_required
def add_marriage(family_tree, member_id):
    person_a = get_member_or_404(family_tree, member_id)
    person_b, error = get_related_member("spouse_id", family_tree)
    start_year, start_error = parse_optional_int(request.form.get("start_year", ""), "Start year")
    end_year, end_error = parse_optional_int(request.form.get("end_year", ""), "End year")
    error = error or start_error or end_error
    if error is None:
        error = validate_marriage(person_a, person_b, start_year, end_year)
    if error:
        return render_relationship_error(family_tree, person_a, error), 400

    db.session.add(
        Marriage(
            family_tree_id=family_tree.id,
            person_a_id=person_a.id,
            person_b_id=person_b.id,
            start_year=start_year,
            end_year=end_year,
        )
    )
    db.session.commit()
    return redirect(
        url_for("relationships.detail", tree_id=family_tree.id, member_id=person_a.id)
    )


@bp.post("/relationships/parent-child/<int:relationship_id>/delete")
@relationship_tree_required
def delete_parent_child(family_tree, relationship_id):
    relationship = get_relationship_or_404(
        ParentChildRelationship,
        family_tree,
        relationship_id,
    )
    member_id = relationship.child_id
    db.session.delete(relationship)
    db.session.commit()
    return redirect(
        url_for("relationships.detail", tree_id=family_tree.id, member_id=member_id)
    )


@bp.post("/relationships/marriages/<int:relationship_id>/delete")
@relationship_tree_required
def delete_marriage(family_tree, relationship_id):
    relationship = get_relationship_or_404(Marriage, family_tree, relationship_id)
    member_id = relationship.person_a_id
    db.session.delete(relationship)
    db.session.commit()
    return redirect(
        url_for("relationships.detail", tree_id=family_tree.id, member_id=member_id)
    )


def render_relationship_error(family_tree, member, error):
    marriages = (
        Marriage.query.filter_by(family_tree_id=family_tree.id, person_a_id=member.id).all()
        + Marriage.query.filter_by(family_tree_id=family_tree.id, person_b_id=member.id).all()
    )
    return render_template(
        "relationships/detail.html",
        family_tree=family_tree,
        member=member,
        marriages=marriages,
        spouse_for=spouse_for,
        error=error,
    )
