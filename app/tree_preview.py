from flask import Blueprint, abort, render_template, request

from .auth import login_required
from .members import accessible_tree_required, get_member_or_404
from .models import Member, ParentChildRelationship


bp = Blueprint("tree_preview", __name__, url_prefix="/family-trees/<int:tree_id>")


def build_descendant_tree(member, visited=None):
    if visited is None:
        visited = set()

    repeated = member.id in visited
    node = {
        "member": member,
        "children": [],
        "repeated": repeated,
    }
    if repeated:
        return node

    visited.add(member.id)
    child_links = (
        ParentChildRelationship.query.filter_by(parent_id=member.id)
        .order_by(ParentChildRelationship.child_id)
        .all()
    )
    for link in child_links:
        node["children"].append(build_descendant_tree(link.child, visited.copy()))
    return node


@bp.get("/tree-preview")
@login_required
@accessible_tree_required
def index(family_tree):
    root_member_id = request.args.get("root_member_id", "").strip()
    root_member = None
    tree = None

    if root_member_id:
        try:
            member_id = int(root_member_id)
        except ValueError:
            abort(404)
        root_member = get_member_or_404(family_tree, member_id)
        tree = build_descendant_tree(root_member)

    return render_template(
        "tree_preview/index.html",
        family_tree=family_tree,
        root_member=root_member,
        tree=tree,
        root_member_id=root_member_id,
    )
