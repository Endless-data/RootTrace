import csv
import io
import zipfile
from datetime import date
from functools import wraps

from flask import Blueprint, abort, g, redirect, render_template, request, send_file, url_for

from .auth import login_required
from .dashboard import family_tree_member_stats
from .extensions import db
from .models import FamilyTree, FamilyTreeCollaborator, Marriage, Member, ParentChildRelationship, User


bp = Blueprint("family_trees", __name__, url_prefix="/family-trees")

MEMBER_CSV_COLUMNS = [
    "id",
    "family_tree_id",
    "name",
    "gender",
    "birth_year",
    "death_year",
    "generation",
    "biography",
    "created_at",
]
PARENT_CHILD_CSV_COLUMNS = ["id", "family_tree_id", "parent_id", "child_id", "relationship_type"]
MARRIAGE_CSV_COLUMNS = ["id", "family_tree_id", "person_a_id", "person_b_id", "start_year", "end_year"]


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


def parse_required_int(raw_value, field_name):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} 必须是整数。") from None


def parse_optional_int(raw_value, field_name):
    if raw_value is None or raw_value == "":
        return None
    return parse_required_int(raw_value, field_name)


def read_uploaded_csv(file_storage, required_columns, label, required=False):
    if file_storage is None or file_storage.filename == "":
        if required:
            raise ValueError(f"请上传 {label}。")
        return []

    content = file_storage.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise ValueError(f"{label} 不能为空。")

    missing_columns = [column for column in required_columns if column not in reader.fieldnames]
    if missing_columns:
        raise ValueError(f"{label} 缺少列：{', '.join(missing_columns)}。")

    return list(reader)


def import_family_tree_csvs(family_tree, files):
    member_rows = read_uploaded_csv(files.get("members_csv"), MEMBER_CSV_COLUMNS, "members.csv", required=True)
    parent_child_rows = read_uploaded_csv(
        files.get("parent_child_relationships_csv"),
        PARENT_CHILD_CSV_COLUMNS,
        "parent_child_relationships.csv",
    )
    marriage_rows = read_uploaded_csv(files.get("marriages_csv"), MARRIAGE_CSV_COLUMNS, "marriages.csv")

    uploaded_member_ids = set()
    imported_member_ids = {}
    for row in member_rows:
        uploaded_id = parse_required_int(row.get("id"), "members.csv 的 id")
        if uploaded_id in uploaded_member_ids:
            raise ValueError(f"members.csv 存在重复成员 id：{uploaded_id}。")
        uploaded_member_ids.add(uploaded_id)

        name = (row.get("name") or "").strip()
        if not name:
            raise ValueError("members.csv 的 name 不能为空。")

        member = Member(
            family_tree_id=family_tree.id,
            name=name,
            gender=(row.get("gender") or "unknown").strip() or "unknown",
            birth_year=parse_optional_int(row.get("birth_year"), "members.csv 的 birth_year"),
            death_year=parse_optional_int(row.get("death_year"), "members.csv 的 death_year"),
            generation=parse_optional_int(row.get("generation"), "members.csv 的 generation"),
            biography=row.get("biography") or "",
        )
        db.session.add(member)
        db.session.flush()
        imported_member_ids[uploaded_id] = member.id

    seen_parent_child = set()
    for row in parent_child_rows:
        parent_uploaded_id = parse_required_int(row.get("parent_id"), "parent_child_relationships.csv 的 parent_id")
        child_uploaded_id = parse_required_int(row.get("child_id"), "parent_child_relationships.csv 的 child_id")
        relationship_type = (row.get("relationship_type") or "").strip()
        if relationship_type not in {"father", "mother"}:
            raise ValueError("parent_child_relationships.csv 的 relationship_type 必须是 father 或 mother。")
        if parent_uploaded_id not in imported_member_ids or child_uploaded_id not in imported_member_ids:
            raise ValueError("parent_child_relationships.csv 引用了本次 members.csv 中不存在的成员 id。")

        parent_id = imported_member_ids[parent_uploaded_id]
        child_id = imported_member_ids[child_uploaded_id]
        key = (parent_id, child_id, relationship_type)
        if key in seen_parent_child:
            raise ValueError("parent_child_relationships.csv 存在重复亲子关系。")
        seen_parent_child.add(key)
        db.session.add(
            ParentChildRelationship(
                family_tree_id=family_tree.id,
                parent_id=parent_id,
                child_id=child_id,
                relationship_type=relationship_type,
            )
        )

    seen_marriages = set()
    for row in marriage_rows:
        person_a_uploaded_id = parse_required_int(row.get("person_a_id"), "marriages.csv 的 person_a_id")
        person_b_uploaded_id = parse_required_int(row.get("person_b_id"), "marriages.csv 的 person_b_id")
        if person_a_uploaded_id not in imported_member_ids or person_b_uploaded_id not in imported_member_ids:
            raise ValueError("marriages.csv 引用了本次 members.csv 中不存在的成员 id。")

        person_a_id = imported_member_ids[person_a_uploaded_id]
        person_b_id = imported_member_ids[person_b_uploaded_id]
        key = tuple(sorted((person_a_id, person_b_id)))
        if key in seen_marriages:
            raise ValueError("marriages.csv 存在重复婚姻关系。")
        seen_marriages.add(key)
        db.session.add(
            Marriage(
                family_tree_id=family_tree.id,
                person_a_id=person_a_id,
                person_b_id=person_b_id,
                start_year=parse_optional_int(row.get("start_year"), "marriages.csv 的 start_year"),
                end_year=parse_optional_int(row.get("end_year"), "marriages.csv 的 end_year"),
            )
        )

    return {
        "members": len(member_rows),
        "parent_child_relationships": len(parent_child_rows),
        "marriages": len(marriage_rows),
    }


def write_csv_to_string(columns, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build_family_tree_export_zip(family_tree):
    members = [
        {
            "id": member.id,
            "family_tree_id": member.family_tree_id,
            "name": member.name,
            "gender": member.gender,
            "birth_year": member.birth_year or "",
            "death_year": member.death_year or "",
            "generation": member.generation or "",
            "biography": member.biography,
            "created_at": member.created_at.isoformat() if member.created_at else "",
        }
        for member in Member.query.filter_by(family_tree_id=family_tree.id).order_by(Member.id).all()
    ]
    parent_child_relationships = [
        {
            "id": relationship.id,
            "family_tree_id": relationship.family_tree_id,
            "parent_id": relationship.parent_id,
            "child_id": relationship.child_id,
            "relationship_type": relationship.relationship_type,
        }
        for relationship in ParentChildRelationship.query.filter_by(family_tree_id=family_tree.id)
        .order_by(ParentChildRelationship.id)
        .all()
    ]
    marriages = [
        {
            "id": marriage.id,
            "family_tree_id": marriage.family_tree_id,
            "person_a_id": marriage.person_a_id,
            "person_b_id": marriage.person_b_id,
            "start_year": marriage.start_year or "",
            "end_year": marriage.end_year or "",
        }
        for marriage in Marriage.query.filter_by(family_tree_id=family_tree.id).order_by(Marriage.id).all()
    ]

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("members.csv", write_csv_to_string(MEMBER_CSV_COLUMNS, members))
        zip_file.writestr(
            "parent_child_relationships.csv",
            write_csv_to_string(PARENT_CHILD_CSV_COLUMNS, parent_child_relationships),
        )
        zip_file.writestr("marriages.csv", write_csv_to_string(MARRIAGE_CSV_COLUMNS, marriages))
    archive.seek(0)
    return archive


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
    return render_template(
        "family_trees/detail.html",
        family_tree=family_tree,
        stats=family_tree_member_stats(family_tree.id),
    )


@bp.get("/<int:tree_id>/import-export")
@login_required
def import_export(tree_id):
    family_tree = db.session.get(FamilyTree, tree_id)
    if family_tree is None:
        abort(404)
    if not can_access_family_tree(g.user, family_tree):
        abort(403)
    return render_template("family_trees/import_export.html", family_tree=family_tree)


@bp.post("/<int:tree_id>/import")
@login_required
def import_csv(tree_id):
    family_tree = db.session.get(FamilyTree, tree_id)
    if family_tree is None:
        abort(404)
    if not can_access_family_tree(g.user, family_tree):
        abort(403)

    try:
        summary = import_family_tree_csvs(family_tree, request.files)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return render_template("family_trees/import_export.html", family_tree=family_tree, error=str(error)), 400

    return render_template("family_trees/import_export.html", family_tree=family_tree, import_summary=summary)


@bp.get("/<int:tree_id>/export.zip")
@login_required
def export_zip(tree_id):
    family_tree = db.session.get(FamilyTree, tree_id)
    if family_tree is None:
        abort(404)
    if not can_access_family_tree(g.user, family_tree):
        abort(403)

    archive = build_family_tree_export_zip(family_tree)
    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"roottrace-family-tree-{family_tree.id}.zip",
    )


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
            stats=family_tree_member_stats(family_tree.id),
            error="User does not exist.",
        ), 400
    if user.id == family_tree.created_by_user_id:
        return render_template(
            "family_trees/detail.html",
            family_tree=family_tree,
            stats=family_tree_member_stats(family_tree.id),
            error="Creator cannot be invited.",
        ), 400
    if any(collaboration.user_id == user.id for collaboration in family_tree.collaborators):
        return render_template(
            "family_trees/detail.html",
            family_tree=family_tree,
            stats=family_tree_member_stats(family_tree.id),
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
