from collections import deque

from flask import Blueprint, abort, render_template, request

from .auth import login_required
from .members import accessible_tree_required, get_member_or_404
from .models import Marriage, ParentChildRelationship


bp = Blueprint("relationship_paths", __name__, url_prefix="/family-trees/<int:tree_id>")


def neighbors_for_member(member_id, family_tree_id):
    neighbors = []

    parent_links = ParentChildRelationship.query.filter_by(
        family_tree_id=family_tree_id,
        child_id=member_id,
    ).all()
    for link in parent_links:
        neighbors.append((link.parent, f"child-{link.relationship_type}"))

    child_links = ParentChildRelationship.query.filter_by(
        family_tree_id=family_tree_id,
        parent_id=member_id,
    ).all()
    for link in child_links:
        neighbors.append((link.child, f"{link.relationship_type}-child"))

    marriages = (
        Marriage.query.filter_by(family_tree_id=family_tree_id, person_a_id=member_id).all()
        + Marriage.query.filter_by(family_tree_id=family_tree_id, person_b_id=member_id).all()
    )
    for marriage in marriages:
        spouse = marriage.person_b if marriage.person_a_id == member_id else marriage.person_a
        neighbors.append((spouse, "spouse"))

    return sorted(neighbors, key=lambda item: (item[0].id, item[1]))


def find_relationship_path(source, target, family_tree_id):
    if source.id == target.id:
        return []

    queue = deque([(source, [])])
    visited = {source.id}

    while queue:
        current, path = queue.popleft()
        for neighbor, label in neighbors_for_member(current.id, family_tree_id):
            if neighbor.id in visited:
                continue
            next_step = {
                "from": current,
                "to": neighbor,
                "label": label,
            }
            next_path = path + [next_step]
            if neighbor.id == target.id:
                return next_path
            visited.add(neighbor.id)
            queue.append((neighbor, next_path))

    return None


def parse_member_id(raw_value):
    raw_value = raw_value.strip()
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError:
        abort(404)


@bp.get("/relationship-path")
@login_required
@accessible_tree_required
def index(family_tree):
    source_member_id_raw = request.args.get("source_member_id", "").strip()
    target_member_id_raw = request.args.get("target_member_id", "").strip()
    source = None
    target = None
    path = None
    submitted = bool(source_member_id_raw or target_member_id_raw)

    if submitted:
        source_member_id = parse_member_id(source_member_id_raw)
        target_member_id = parse_member_id(target_member_id_raw)
        if source_member_id is None or target_member_id is None:
            abort(404)
        source = get_member_or_404(family_tree, source_member_id)
        target = get_member_or_404(family_tree, target_member_id)
        path = find_relationship_path(source, target, family_tree.id)

    return render_template(
        "relationship_paths/index.html",
        family_tree=family_tree,
        source=source,
        target=target,
        path=path,
        submitted=submitted,
        source_member_id=source_member_id_raw,
        target_member_id=target_member_id_raw,
    )
