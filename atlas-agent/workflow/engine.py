from typing import Any

from mcp_client.router import MCPRouter

from .definitions import (
    is_talent_evaluation_query,
    is_workflow_query,
    parse_talent_evaluation,
    parse_unit_conversion_chain,
)
from .models import (
    WorkflowResult,
    WorkflowStepResult,
)


def extract_structured_result(result: Any) -> dict:
    """
    Extract structured output returned by an MCP tool.
    """

    if getattr(result, "is_error", False):
        raise RuntimeError(
            "MCP tool returned an error."
        )

    structured = getattr(
        result,
        "structured_content",
        None,
    )

    if isinstance(structured, dict):
        return structured

    raise RuntimeError(
        "MCP tool did not return structured content."
    )


class WorkflowEngine:
    """
    Executes multi-step workflows.

    Responsibilities:
    - Maintain workflow execution state
    - Execute steps sequentially
    - Pass previous outputs into later steps
    - Invoke MCP tools through MCPRouter

    The workflow engine does NOT:
    - connect directly to MCP servers
    - perform business calculations
    """

    def __init__(self, router: MCPRouter):
        self.router = router
        self.execution_history: list[WorkflowResult] = []

    async def execute(self, query: str):
        """
        Main workflow/orchestration entry point.
        """

        query = query.strip()

        if not query:
            raise ValueError("Query cannot be empty.")

        # ---------------------------------------------------------
        # Talent Intelligence workflow
        # ---------------------------------------------------------

        if is_talent_evaluation_query(query):
            workflow_input = parse_talent_evaluation(query)

            if workflow_input is None:
                raise ValueError(
                    "I could not understand the talent evaluation request."
                )

            return await self.run_talent_evaluation(
                resume_text=workflow_input["resume_text"],
                job_description=workflow_input["job_description"],
            )

        # ---------------------------------------------------------
        # Existing unit conversion workflow
        # ---------------------------------------------------------

        if is_workflow_query(query):
            workflow_input = parse_unit_conversion_chain(query)

            if workflow_input is None:
                raise ValueError(
                    "I could not understand the workflow request."
                )

            return await self.run_unit_conversion_chain(
                value=workflow_input["value"],
                from_unit=workflow_input["from_unit"],
                intermediate_unit=workflow_input["intermediate_unit"],
                to_unit=workflow_input["to_unit"],
            )

        # ---------------------------------------------------------
        # Single-step requests
        # ---------------------------------------------------------

        return await self.router.route(query)

    async def run_talent_evaluation(
        self,
        resume_text: str,
        job_description: str,
    ) -> WorkflowResult:

        workflow_name = "talent_candidate_evaluation"

        steps: list[WorkflowStepResult] = []

        try:
            # -----------------------------------------------------
            # STEP 1 - Resume analysis
            # -----------------------------------------------------

            resume_arguments = {
                "resume_text": resume_text,
            }

            resume_result = await self.router.call_tool(
                "inspect_resume",
                resume_arguments,
            )

            resume_data = extract_structured_result(
                resume_result
            )

            steps.append(
                WorkflowStepResult(
                    step_name="inspect_resume",
                    tool_name="inspect_resume",
                    status="success",
                    arguments=resume_arguments,
                    result=resume_data,
                )
            )

            candidate_data = resume_data["data"]

            # -----------------------------------------------------
            # STEP 2 - Job analysis
            # -----------------------------------------------------

            job_arguments = {
                "job_description": job_description,
            }

            job_result = await self.router.call_tool(
                "analyze_job",
                job_arguments,
            )

            job_data = extract_structured_result(
                job_result
            )

            steps.append(
                WorkflowStepResult(
                    step_name="analyze_job",
                    tool_name="analyze_job",
                    status="success",
                    arguments=job_arguments,
                    result=job_data,
                )
            )

            job_requirements = job_data["data"]

            # -----------------------------------------------------
            # STEP 3 - Skill matching
            # -----------------------------------------------------

            matching_arguments = {
                "candidate_skills": candidate_data["skills"],
                "required_skills": job_requirements[
                    "required_skills"
                ],
            }

            matching_result = await self.router.call_tool(
                "compare_skills",
                matching_arguments,
            )

            matching_data = extract_structured_result(
                matching_result
            )

            steps.append(
                WorkflowStepResult(
                    step_name="compare_skills",
                    tool_name="compare_skills",
                    status="success",
                    arguments=matching_arguments,
                    result=matching_data,
                )
            )

            # -----------------------------------------------------
            # Final workflow output
            # -----------------------------------------------------

            match_data = matching_data["data"]

            output = {
                "candidate_name": candidate_data[
                    "candidate_name"
                ],
                "job_title": job_requirements[
                    "title"
                ],
                "candidate_skills": candidate_data[
                    "skills"
                ],
                "required_skills": job_requirements[
                    "required_skills"
                ],
                "matched_skills": match_data[
                    "matched"
                ],
                "missing_skills": match_data[
                    "missing"
                ],
                "match_percentage": match_data[
                    "match_percentage"
                ],
            }

            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                status="success",
                steps=steps,
                output=output,
            )

            self.execution_history.append(
                workflow_result
            )

            return workflow_result

        except Exception as exc:

            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                status="failed",
                steps=steps,
                error=str(exc),
            )

            self.execution_history.append(
                workflow_result
            )

            return workflow_result

    async def run_unit_conversion_chain(
        self,
        value: float,
        from_unit: str,
        intermediate_unit: str,
        to_unit: str,
    ) -> WorkflowResult:

        workflow_name = "unit_conversion_chain"

        steps: list[WorkflowStepResult] = []

        try:
            # -----------------------------------------------------
            # STEP 1
            # -----------------------------------------------------

            first_arguments = {
                "value": value,
                "from_unit": from_unit,
                "to_unit": intermediate_unit,
            }

            first_result = await self.router.call_tool(
                "convert_units",
                first_arguments,
            )

            first_data = extract_structured_result(
                first_result
            )

            steps.append(
                WorkflowStepResult(
                    step_name="convert_to_intermediate_unit",
                    tool_name="convert_units",
                    status="success",
                    arguments=first_arguments,
                    result=first_data,
                )
            )

            intermediate_value = float(
                first_data["result"]
            )

            # -----------------------------------------------------
            # STEP 2
            # -----------------------------------------------------

            second_arguments = {
                "value": intermediate_value,
                "from_unit": intermediate_unit,
                "to_unit": to_unit,
            }

            second_result = await self.router.call_tool(
                "convert_units",
                second_arguments,
            )

            second_data = extract_structured_result(
                second_result
            )

            steps.append(
                WorkflowStepResult(
                    step_name="convert_to_final_unit",
                    tool_name="convert_units",
                    status="success",
                    arguments=second_arguments,
                    result=second_data,
                )
            )

            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                status="success",
                steps=steps,
                output=second_data,
            )

            self.execution_history.append(
                workflow_result
            )

            return workflow_result

        except Exception as exc:
            workflow_result = WorkflowResult(
                workflow_name=workflow_name,
                status="failed",
                steps=steps,
                error=str(exc),
            )

            self.execution_history.append(
                workflow_result
            )

            return workflow_result