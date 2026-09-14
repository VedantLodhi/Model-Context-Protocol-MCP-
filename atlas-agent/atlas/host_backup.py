from mcp_client.router import MCPRouter

from .memory import AtlasMemory
from .models import ExecutionRecord


class AtlasHost:
    """
    User-facing Atlas host.

    Responsibilities:
    - Receive user queries
    - Resolve follow-up queries using conversation context
    - Send new computational queries to the MCP Router
    - Maintain conversation memory
    - Maintain structured execution history
    - Format MCP results for the user

    AtlasHost does NOT:
    - Connect directly to MCP servers
    - Detect MCP intent for new requests
    - Select MCP tools
    - Perform algebra/unit/date calculations
    """

    def __init__(self, router: MCPRouter):
        self.router = router
        self.memory = AtlasMemory()

    async def handle_query(self, query: str) -> str:
        """
        Process one user query.
        """

        query = query.strip()

        if not query:
            return "Please enter a query."

        is_follow_up = self._is_follow_up(query)

        # ---------------------------------------------------------
        # Follow-up request
        # ---------------------------------------------------------
        #
        # Follow-ups are handled directly by Atlas using memory.
        # They do NOT trigger another MCP call.
        #
        if is_follow_up:
            response = self._answer_follow_up(query)

            if response is not None:
                self.memory.add_execution(
                    ExecutionRecord(
                        query=query,
                        intent="algebra",
                        tool_name="Atlas Memory",
                        result=response,
                        status="success",
                        follow_up=True,
                    )
                )

                self.memory.add_turn(
                    query,
                    response,
                )

                return response

        # ---------------------------------------------------------
        # New request
        # ---------------------------------------------------------

        try:
            route_result = await self.router.route(query)

        except Exception as exc:
            response = (
                "I could not process that request. "
                f"Reason: {exc}"
            )

            self.memory.add_execution(
                ExecutionRecord(
                    query=query,
                    intent="unknown",
                    tool_name=None,
                    result=None,
                    status="error",
                    follow_up=False,
                )
            )

            self.memory.add_turn(
                query,
                response,
            )

            return response

        # ---------------------------------------------------------
        # Router returned an error
        # ---------------------------------------------------------

        if route_result.error:
            response = route_result.error

            self.memory.add_execution(
                ExecutionRecord(
                    query=query,
                    intent=route_result.intent,
                    tool_name=route_result.tool_name,
                    result=None,
                    status="error",
                    follow_up=False,
                )
            )

            self.memory.add_turn(
                query,
                response,
            )

            return response

        # ---------------------------------------------------------
        # Successful MCP result
        # ---------------------------------------------------------

        response = self._format_result(
            route_result
        )

        # Store the result as the active context.
        self.memory.set_result(
            route_result.intent,
            route_result.data,
        )

        self.memory.add_execution(
            ExecutionRecord(
                query=query,
                intent=route_result.intent,
                tool_name=route_result.tool_name,
                result=route_result.data,
                status="success",
                follow_up=False,
            )
        )

        self.memory.add_turn(
            query,
            response,
        )

        return response

    def show_history(self) -> None:
        """Display current conversation history."""

        self.memory.show_history()

    def show_execution_history(self) -> None:
        """Display structured MCP execution history."""

        self.memory.show_execution_history()

    def clear_memory(self) -> None:
        """Clear current conversation and execution memory."""

        self.memory.clear()

    def _is_follow_up(self, query: str) -> bool:
        """
        Determine whether the query refers to
        a previous conversation result.
        """

        normalized = query.strip().lower()

        follow_up_phrases = (
            "larger",
            "bigger",
            "greater",
            "smaller",
            "lower",
            "second solution",
            "first solution",
            "which solution",
            "which one",
            "what about",
        )

        return any(
            phrase in normalized
            for phrase in follow_up_phrases
        )

    def _answer_follow_up(
        self,
        query: str,
    ) -> str | None:
        """
        Answer simple algebra follow-up questions
        directly from Atlas memory.

        No MCP call is made here.
        """

        normalized = query.strip().lower()

        if self.memory.last_algebra_result is None:
            return None

        try:
            content = (
                self.memory.last_algebra_result.structured_content
            )

            solutions = content["solution"]

            if not isinstance(solutions, list):
                return None

            if not solutions:
                return None

            numeric_solutions = [
                float(value)
                for value in solutions
            ]

            if (
                "larger" in normalized
                or "bigger" in normalized
                or "greater" in normalized
            ):
                largest = max(numeric_solutions)

                return (
                    f"The larger solution is "
                    f"{self._format_number(largest)}."
                )

            if (
                "smaller" in normalized
                or "lower" in normalized
            ):
                smallest = min(numeric_solutions)

                return (
                    f"The smaller solution is "
                    f"{self._format_number(smallest)}."
                )

            if "second solution" in normalized:
                if len(solutions) >= 2:
                    return (
                        f"The second solution is "
                        f"{solutions[1]}."
                    )

            if "first solution" in normalized:
                if len(solutions) >= 1:
                    return (
                        f"The first solution is "
                        f"{solutions[0]}."
                    )

        except (
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ):
            return None

        return None

    @staticmethod
    def _format_number(value: float) -> str:
        """
        Format integer-like floats without .0.
        """

        if value.is_integer():
            return str(int(value))

        return str(value)

    @staticmethod
    def _format_result(route_result) -> str:
        """
        Convert an MCP result into a user-facing response.
        """

        data = route_result.data

        if route_result.intent == "algebra":
            content = data.structured_content

            steps = " -> ".join(
                content["steps"]
            )

            return (
                f"Problem: {content['problem']}\n"
                f"Solution: {content['solution']}\n"
                f"Steps: {steps}"
            )

        if route_result.intent == "unit":
            content = data.structured_content

            return (
                f"{content['value']} "
                f"{content['from_unit']} = "
                f"{content['result']} "
                f"{content['result_unit']}"
            )

        if route_result.intent == "datetime":
            content = data.structured_content

            return (
                f"Current time in "
                f"{content['timezone']}: "
                f"{content['datetime']}"
            )

        return str(data)