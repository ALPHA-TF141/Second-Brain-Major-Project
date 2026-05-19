from collections import defaultdict

from app.models.memory import MemoryTag
from app.models.semantic import MemoryCluster


class MemoryClusterer:
    def rebuild_clusters(self, db):
        db.query(MemoryCluster).delete()
        grouped = defaultdict(list)
        rows = db.query(MemoryTag).all()
        for row in rows:
            grouped[row.tag].append(row.memory_id)

        created = 0
        for tag, memory_ids in grouped.items():
            unique_ids = sorted(set(memory_ids))
            if len(unique_ids) < 2:
                continue
            db.add(
                MemoryCluster(
                    label=tag,
                    description=f"Memories connected by repeated concept: {tag}",
                    memory_ids=",".join(str(memory_id) for memory_id in unique_ids),
                    size=len(unique_ids),
                )
            )
            created += 1
        db.commit()
        return {"clusters": created}


memory_clusterer = MemoryClusterer()
