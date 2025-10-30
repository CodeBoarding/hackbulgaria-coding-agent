"""Extractors for structured output from agent responses using trustcall."""

from trustcall import create_extractor
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.models import PlanOutput, ImplementationReport, ValidationReport
from src.config import get_google_api_key, MODEL_NAME


# Initialize LLM for extractors
_extractor_llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.0,  # Use lower temperature for structured extraction
    google_api_key=get_google_api_key()
)

# Create extractors for each agent output type
plan_extractor = create_extractor(
    _extractor_llm,
    tools=[PlanOutput],
    tool_choice="PlanOutput"
)

implementation_extractor = create_extractor(
    _extractor_llm,
    tools=[ImplementationReport],
    tool_choice="ImplementationReport"
)

validation_extractor = create_extractor(
    _extractor_llm,
    tools=[ValidationReport],
    tool_choice="ValidationReport"
)


def extract_plan(text: str) -> PlanOutput:
    """Extract structured plan from agent text response.
    
    Args:
        text: Agent response text
        
    Returns:
        PlanOutput object extracted from the text
    """
    try:
        result = plan_extractor.invoke(
            f"""Extract the execution plan from the following agent response:
<response>
{text}
</response>"""
        )
        # trustcall returns a dict with "responses" key containing tool calls
        return result["responses"][0]
    except Exception as e:
        print(f"Warning: Failed to extract plan: {e}")
        # Fallback: return minimal plan
        return PlanOutput(
            analysis="Failed to extract structured plan from agent response",
            context=text[:500] if len(text) > 500 else text,
            steps=[]
        )


def extract_implementation(text: str) -> ImplementationReport:
    """Extract structured implementation report from agent text response.
    
    Args:
        text: Agent response text
        
    Returns:
        ImplementationReport object extracted from the text
    """
    try:
        result = implementation_extractor.invoke(
            f"""Extract the implementation report from the following agent response:
<response>
{text}
</response>"""
        )
        # trustcall returns a dict with "responses" key containing tool calls
        return result["responses"][0]
    except Exception as e:
        print(f"Warning: Failed to extract implementation report: {e}")
        # Fallback: return minimal report
        return ImplementationReport(
            status="failed",
            summary=f"Failed to extract report from response. Error: {str(e)}"
        )


def extract_validation(text: str) -> ValidationReport:
    """Extract structured validation report from agent text response.
    
    Args:
        text: Agent response text
        
    Returns:
        ValidationReport object extracted from the text
    """
    try:
        result = validation_extractor.invoke(
            f"""Extract the validation report from the following agent response:
<response>
{text}
</response>"""
        )
        # trustcall returns a dict with "responses" key containing tool calls
        return result["responses"][0]
    except Exception as e:
        print(f"Warning: Failed to extract validation report: {e}")
        # Fallback: return report with needs_fixes
        return ValidationReport(
            status="needs_fixes",
            changes_summary=f"Failed to extract validation from response. Error: {str(e)}",
            overall_quality="needs_improvement",
            approval=False
        )
