from collections import defaultdict


class MemoryTimelineBuilder:
    def group_by_day(self, memories):
        groups = defaultdict(list)
        for memory in memories:
            key = memory.created_at.date().isoformat() if memory.created_at else "unknown"
            groups[key].append(memory)
        return [{"date": date, "items": items} for date, items in sorted(groups.items(), reverse=True)]

    def group_by_week(self, memories):
        groups = defaultdict(list)
        for memory in memories:
            year, week, _weekday = memory.created_at.isocalendar()
            groups[f"{year}-W{week:02d}"].append(memory)
        return [{"week": week, "items": items} for week, items in sorted(groups.items(), reverse=True)]


memory_timeline_builder = MemoryTimelineBuilder()
