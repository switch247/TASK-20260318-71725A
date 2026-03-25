"""Handle process decision outcomes and derive final instance state transitions."""

from src.models.enums import TaskStatus
from src.models.process import ProcessTaskAssignment


class ProcessDecisionHandler:
    def determine_completion(self, tasks: list[ProcessTaskAssignment]) -> tuple[bool, bool]:
        has_rejection = any(item.task_status == TaskStatus.REJECTED for item in tasks)
        all_done = all(
            item.task_status in [TaskStatus.APPROVED, TaskStatus.REJECTED] for item in tasks
        )
        return has_rejection, all_done
