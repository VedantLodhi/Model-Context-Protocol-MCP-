from types import SimpleNamespace

from .models import ExecutionRecord
from .storage import AtlasStorage


class AtlasMemory:
    """
    Stores Atlas conversation state.

    SQLite provides persistence across Atlas restarts.
    """

    def __init__(self):
        self.storage = AtlasStorage()

        self.history: list[dict[str, str]] = (
            self.storage.load_history()
        )

        self.execution_history: list[
            ExecutionRecord
        ] = []

        self.last_intent: str | None = None
        self.last_result = None
        self.last_algebra_result = None

        self._restore_execution_history()

    def add_turn(
        self,
        user_query: str,
        atlas_response: str,
    ) -> None:

        self.history.append(
            {
                "user": user_query,
                "atlas": atlas_response,
            }
        )

        self.storage.save_turn(
            user_query,
            atlas_response,
        )

    def add_execution(
        self,
        record: ExecutionRecord,
    ) -> None:

        self.execution_history.append(
            record
        )

        self.storage.save_execution(
            query=record.query,
            intent=record.intent,
            tool_name=record.tool_name,
            result=record.result,
            status=record.status,
            follow_up=record.follow_up,
        )

    def set_result(
        self,
        intent: str,
        result,
    ) -> None:

        self.last_intent = intent
        self.last_result = result

        if intent == "algebra":
            self.last_algebra_result = result

    def clear(self) -> None:

        self.history.clear()
        self.execution_history.clear()

        self.last_intent = None
        self.last_result = None
        self.last_algebra_result = None

        self.storage.clear()

    def _restore_execution_history(self) -> None:
        """
        Restore persisted execution records into
        the in-memory representation used by Atlas.
        """

        records = self.storage.load_executions()

        for item in records:
            result = self._restore_result(
                item["result"],
                item["intent"],
            )

            record = ExecutionRecord(
                query=item["query"],
                intent=item["intent"],
                tool_name=item["tool_name"],
                result=result,
                status=item["status"],
                follow_up=item["follow_up"],
            )

            self.execution_history.append(
                record
            )

            # Restore the most recent algebra result
            # so simple follow-ups can continue working.
            if (
                item["intent"] == "algebra"
                and item["status"] == "success"
                and result is not None
            ):
                self.last_algebra_result = result
                self.last_intent = "algebra"
                self.last_result = result

    @staticmethod
    def _restore_result(
        result,
        intent: str,
    ):
        """
        Restore persisted result into the minimum
        object shape required by Atlas.
        """

        if result is None:
            return None

        if intent == "algebra":
            return SimpleNamespace(
                structured_content=result
            )

        if intent == "unit":
            return SimpleNamespace(
                structured_content=result
            )

        if intent == "datetime":
            return SimpleNamespace(
                structured_content=result
            )

        if intent == "workflow":
            return AtlasMemory._restore_workflow(
                result
            )

        return result

    @staticmethod
    def _restore_workflow(result):
        """
        Rebuild the workflow dataclasses from
        persisted JSON.
        """

        from workflow.models import (
            WorkflowResult,
            WorkflowStepResult,
        )

        steps = []

        for step in result.get(
            "steps",
            [],
        ):
            steps.append(
                WorkflowStepResult(
                    step_name=step.get(
                        "step_name",
                        "",
                    ),
                    tool_name=step.get(
                        "tool_name",
                        "",
                    ),
                    status=step.get(
                        "status",
                        "",
                    ),
                    arguments=step.get(
                        "arguments"
                    ),
                    result=step.get(
                        "result"
                    ),
                    error=step.get(
                        "error"
                    ),
                )
            )

        return WorkflowResult(
            workflow_name=result.get(
                "workflow_name",
                "",
            ),
            status=result.get(
                "status",
                "",
            ),
            steps=steps,
            output=result.get(
                "output"
            ),
            error=result.get(
                "error"
            ),
        )

    def show_history(self) -> None:
        print("\n" + "=" * 70)
        print("ATLAS CONVERSATION HISTORY")
        print("=" * 70)

        if not self.history:
            print("\nNo conversation history.")
            print("=" * 70)
            return

        for index, turn in enumerate(
            self.history,
            start=1,
        ):
            print(f"\nTurn {index}")
            print(f"You: {turn['user']}")
            print(f"Atlas: {turn['atlas']}")

        print("\n" + "=" * 70)

    def show_execution_history(self) -> None:
        print("\n" + "=" * 70)
        print("ATLAS EXECUTION HISTORY")
        print("=" * 70)

        if not self.execution_history:
            print("\nNo execution history.")
            print("=" * 70)
            return

        for index, record in enumerate(
            self.execution_history,
            start=1,
        ):
            print(f"\nExecution {index}")
            print(f"Query: {record.query}")
            print(f"Intent: {record.intent}")
            print(f"Tool: {record.tool_name}")
            print(f"Status: {record.status}")
            print(f"Follow-up: {record.follow_up}")

            if (
                record.intent == "workflow"
                and record.result is not None
            ):
                workflow = record.result

                print(
                    f"Workflow: "
                    f"{workflow.workflow_name}"
                )

                print(
                    f"Workflow Status: "
                    f"{workflow.status}"
                )

                for step_number, step in enumerate(
                    workflow.steps,
                    start=1,
                ):
                    print(
                        f"\n  Step {step_number}: "
                        f"{step.step_name}"
                    )

                    print(
                        f"  Tool: "
                        f"{step.tool_name}"
                    )

                    print(
                        f"  Status: "
                        f"{step.status}"
                    )

                    if step.arguments is not None:
                        print(
                            f"  Input: "
                            f"{step.arguments}"
                        )

                    if step.result is not None:
                        print(
                            f"  Output: "
                            f"{step.result}"
                        )

                    if step.error is not None:
                        print(
                            f"  Error: "
                            f"{step.error}"
                        )

                if workflow.output is not None:
                    print(
                        f"\nFinal Output: "
                        f"{workflow.output}"
                    )

                if workflow.error is not None:
                    print(
                        f"\nWorkflow Error: "
                        f"{workflow.error}"
                    )

        print("\n" + "=" * 70)