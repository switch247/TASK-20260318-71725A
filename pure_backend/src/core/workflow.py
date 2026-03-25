from dataclasses import dataclass

from src.core.errors import ValidationError


@dataclass
class WorkflowNode:
    key: str
    assignee_user_id: str
    is_parallel: bool
    is_joint_sign: bool


def parse_workflow_nodes(
    definition_json: str, fallback_assignee_user_id: str
) -> list[WorkflowNode]:
    import json

    try:
        definition = json.loads(definition_json)
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid workflow definition JSON") from exc

    nodes = definition.get("nodes", [])
    if not isinstance(nodes, list) or len(nodes) == 0:
        return [
            WorkflowNode(
                key="review-node-1",
                assignee_user_id=fallback_assignee_user_id,
                is_parallel=False,
                is_joint_sign=False,
            )
        ]

    parsed_nodes: list[WorkflowNode] = []
    for index, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            raise ValidationError("Workflow nodes must be objects")

        key = str(raw_node.get("key", f"node-{index + 1}"))
        assignee_user_id = str(raw_node.get("assignee_user_id") or fallback_assignee_user_id)
        is_parallel = bool(raw_node.get("is_parallel", False))
        is_joint_sign = bool(raw_node.get("is_joint_sign", False))

        condition = raw_node.get("condition")
        if condition is not None and not isinstance(condition, dict):
            raise ValidationError("Node condition must be an object")

        parsed_nodes.append(
            WorkflowNode(
                key=key,
                assignee_user_id=assignee_user_id,
                is_parallel=is_parallel,
                is_joint_sign=is_joint_sign,
            )
        )

    return parsed_nodes
