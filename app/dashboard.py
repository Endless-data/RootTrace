from .models import Member


def family_tree_member_stats(family_tree_id):
    total = Member.query.filter_by(family_tree_id=family_tree_id).count()
    counts = {
        "male": Member.query.filter_by(family_tree_id=family_tree_id, gender="male").count(),
        "female": Member.query.filter_by(family_tree_id=family_tree_id, gender="female").count(),
        "unknown": Member.query.filter_by(
            family_tree_id=family_tree_id,
            gender="unknown",
        ).count(),
    }

    def percent(count):
        if total == 0:
            return "0.0%"
        return f"{(count / total) * 100:.1f}%"

    return {
        "total": total,
        "male": counts["male"],
        "female": counts["female"],
        "unknown": counts["unknown"],
        "male_percent": percent(counts["male"]),
        "female_percent": percent(counts["female"]),
        "unknown_percent": percent(counts["unknown"]),
    }
