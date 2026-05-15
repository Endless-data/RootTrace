from flask import Blueprint, abort, render_template, request

from .auth import login_required
from .members import accessible_tree_required, get_member_or_404
from .models import ParentChildRelationship


bp = Blueprint("ancestors", __name__, url_prefix="/family-trees/<int:tree_id>")


def build_ancestor_tree(member, visited=None):
    if visited is None:
        visited = set()

    repeated = member.id in visited
    node = {
        "member": member,
        "parents": [],
        "repeated": repeated,
    }
    if repeated:
        return node

    visited.add(member.id)
    parent_links = (
        ParentChildRelationship.query.filter_by(child_id=member.id)
        .order_by(ParentChildRelationship.parent_id)
        .all()
    )
    for link in parent_links:
        node["parents"].append(build_ancestor_tree(link.parent, visited.copy()))
    return node


@bp.get("/ancestors")
@login_required
@accessible_tree_required
def index(family_tree):
    member_id_raw = request.args.get("member_id", "").strip()
    member = None
    tree = None

    if member_id_raw:
        try:
            member_id = int(member_id_raw)
        except ValueError:
            abort(404)
        member = get_member_or_404(family_tree, member_id)
        tree = build_ancestor_tree(member)

    return render_template(
        "ancestors/index.html",
        family_tree=family_tree,
        member=member,
        member_id=member_id_raw,
        tree=tree,
    )
