"""Handle process decision outcomes and derive final instance state transitions."""

from src.models.enums import TaskStatus
from src.models.process import ProcessTaskAssignment


class ProcessDecisionHandler:
    def determine_completion(self, tasks: list[ProcessTaskAssignment]) -> tuple[bool, bool]:
        has_rejection = any(item.task_status == TaskStatus.REJECTED for item in tasks)
        parallel_tasks = [item for item in tasks if item.is_parallel]
        joint_tasks = [item for item in tasks if item.is_joint_sign]
        regular_tasks = [item for item in tasks if not item.is_parallel and not item.is_joint_sign]

        regular_done = all(
            item.task_status in [TaskStatus.APPROVED, TaskStatus.REJECTED] for item in regular_tasks
        )
        parallel_done = all(
            item.task_status in [TaskStatus.APPROVED, TaskStatus.REJECTED]
            for item in parallel_tasks
        )
        joint_done = all(item.task_status == TaskStatus.APPROVED for item in joint_tasks)

        all_done = regular_done and parallel_done and joint_done
        return has_rejection, all_done
