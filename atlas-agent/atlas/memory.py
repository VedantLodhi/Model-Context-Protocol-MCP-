from .models import ExecutionRecord


class AtlasMemory:
    """
    Stores Atlas conversation state for the current session.
    """

    def __init__(self):
        self.history: list[dict[str, str]] = []
        self.execution_history: list[ExecutionRecord] = []

        self.last_intent: str | None = None
        self.last_result = None
        self.last_algebra_result = None

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

    def add_execution(
        self,
        record: ExecutionRecord,
    ) -> None:
        self.execution_history.append(record)

    def set_result(
        self,
        intent: str,
        result,
    ) -> None:
        """
        Store the latest primary MCP result.

        Follow-up queries should not overwrite this context.
    """

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

        print("\n" + "=" * 70)