"""Pydantic models for agent outputs."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class FileToCreate(BaseModel):
    """Model for a file that needs to be created."""
    path: str = Field(description="File path to create")
    purpose: str = Field(description="Brief description of what this file does")


class FileToModify(BaseModel):
    """Model for a file that needs to be modified."""
    path: str = Field(description="File path to modify")
    purpose: str = Field(description="Description of what changes are needed")


class ExecutionStep(BaseModel):
    """Model for a single execution step."""
    sequence: int = Field(description="Step number in execution order")
    action: Literal["create", "modify"] = Field(description="Action to perform")
    file: str = Field(description="File path to act on")
    description: str = Field(description="Detailed description of what to do")


class PlanOutput(BaseModel):
    """Structured output from the planning agent."""
    analysis: str = Field(description="Summary of what needs to be done and why")
    context: str = Field(description="Key findings from codebase exploration")
    files_to_create: List[FileToCreate] = Field(
        default_factory=list,
        description="List of files that need to be created"
    )
    files_to_modify: List[FileToModify] = Field(
        default_factory=list,
        description="List of files that need to be modified"
    )
    steps: List[ExecutionStep] = Field(
        description="Ordered list of execution steps"
    )
    considerations: List[str] = Field(
        default_factory=list,
        description="Important edge cases, dependencies, or risks"
    )


class LintingResult(BaseModel):
    """Linting result for a single file."""
    score: float = Field(description="Pylint score out of 10")
    syntax_valid: bool = Field(description="Whether syntax is valid (no AST errors)")
    issues: List[str] = Field(
        default_factory=list,
        description="List of linting issues found"
    )


class ImplementationReport(BaseModel):
    """Structured output from the implementation agent."""
    status: Literal["success", "partial", "failed"] = Field(
        description="Overall status of the implementation"
    )
    files_created: List[str] = Field(
        default_factory=list,
        description="List of file paths that were created"
    )
    files_modified: List[str] = Field(
        default_factory=list,
        description="List of file paths that were modified"
    )
    linting_results: dict[str, LintingResult] = Field(
        default_factory=dict,
        description="Linting results for each Python file"
    )
    summary: str = Field(description="Brief summary of what was implemented")
    issues_encountered: List[str] = Field(
        default_factory=list,
        description="Any problems or deviations from the plan"
    )


class FileQualityAssessment(BaseModel):
    """Quality assessment for a single file."""
    score: float = Field(description="Quality score out of 10")
    syntax_valid: bool = Field(description="Whether syntax is valid")
    issues: List[str] = Field(
        default_factory=list,
        description="List of quality issues found"
    )


class ValidationReport(BaseModel):
    """Structured output from the validator agent."""
    status: Literal["approved", "needs_fixes"] = Field(
        description="Validation status"
    )
    changes_summary: str = Field(description="Summary of changes made based on git diff")
    files_reviewed: List[str] = Field(
        default_factory=list,
        description="List of files that were reviewed"
    )
    quality_assessment: dict[str, FileQualityAssessment] = Field(
        default_factory=dict,
        description="Quality assessment for each file"
    )
    overall_quality: Literal["excellent", "good", "needs_improvement"] = Field(
        description="Overall quality rating"
    )
    issues_found: List[str] = Field(
        default_factory=list,
        description="Specific issues found with file names and line numbers"
    )
    fix_instructions: List[str] = Field(
        default_factory=list,
        description="Specific instructions for fixing issues"
    )
    approval: bool = Field(description="Whether the implementation is approved")
