"""Orchestrator for coordinating multiple agents."""

import json
from typing import Optional, Dict, Any
from src.agent.models import PlanOutput, ImplementationReport, ValidationReport
from src.agent.planning_agent import (
    create_planning_agent,
    extract_plan_from_response,
    PLANNING_AGENT_PROMPT
)
from src.agent.implementation_agent import (
    create_implementation_agent,
    extract_implementation_report,
    IMPLEMENTATION_AGENT_PROMPT
)
from src.agent.validator_agent import (
    create_validator_agent,
    extract_validation_report,
    is_approved,
    VALIDATOR_AGENT_PROMPT
)


def orchestrate_multi_agent(user_request: str, home_directory: Optional[str] = None) -> Dict[str, Any]:
    """Orchestrate multiple agents to handle a coding request.
    
    This function coordinates three specialized agents:
    1. Planning Agent: Creates execution plan (read-only)
    2. Implementation Agent: Executes the plan (read/write)
    3. Validator Agent: Validates implementation (read-only + git)
    
    The flow includes a fix loop where the implementation agent can
    make corrections based on validator feedback (max 3 iterations).
    
    Args:
        user_request: The user's coding request
        home_directory: Optional home directory for file operations
        
    Returns:
        Dictionary containing:
        - plan: The execution plan from planning agent
        - implementation: Implementation report
        - validation: Validation report
        - status: Overall status (approved/needs_review)
        - iterations: Number of fix iterations performed
    """
    print("\n" + "="*70)
    print("MULTI-AGENT ORCHESTRATION")
    print("="*70)
    
    # Phase 1: Planning
    print("\n[PHASE 1: PLANNING]")
    print("-" * 70)
    print("Planning agent analyzing request and creating execution plan...\n")
    
    planning_agent = create_planning_agent(home_directory)
    thread_id = "planning_session"
    
    # Stream planning agent execution to show tools being used
    print("🔍 Planning Agent Working:")
    for chunk in planning_agent.stream(
        {
            "messages": [
                ("system", PLANNING_AGENT_PROMPT),
                ("user", f"Create a detailed execution plan for this request:\n\n{user_request}")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50  # Increase recursion limit
        }
    ):
        _print_agent_activity(chunk)
    
    # Get final response
    plan_response = planning_agent.invoke(
        {
            "messages": [
                ("system", PLANNING_AGENT_PROMPT),
                ("user", f"Create a detailed execution plan for this request:\n\n{user_request}")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }
    )
    
    plan = extract_plan_from_response(plan_response)
    
    print("\n✓ Planning complete!")
    _print_plan_summary(plan)
    
    # Phase 2: Implementation
    print("\n[PHASE 2: IMPLEMENTATION]")
    print("-" * 70)
    print("Implementation agent executing the plan...\n")
    
    implementation_agent = create_implementation_agent(home_directory)
    thread_id = "implementation_session"
    
    # Convert plan to string for the implementation agent - use model_dump_json for Pydantic
    plan_str = plan.model_dump_json(indent=2)
    
    # Stream implementation agent execution
    print("🔧 Implementation Agent Working:")
    for chunk in implementation_agent.stream(
        {
            "messages": [
                ("system", IMPLEMENTATION_AGENT_PROMPT),
                ("user", f"Execute this plan:\n\n{plan_str}")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }
    ):
        _print_agent_activity(chunk)
    
    impl_response = implementation_agent.invoke(
        {
            "messages": [
                ("system", IMPLEMENTATION_AGENT_PROMPT),
                ("user", f"Execute this plan:\n\n{plan_str}")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }
    )
    
    impl_report = extract_implementation_report(impl_response)
    
    print("\n✓ Implementation complete!")
    _print_implementation_summary(impl_report)
    
    # Phase 3: Validation
    print("\n[PHASE 3: VALIDATION]")
    print("-" * 70)
    print("Validator agent reviewing changes...\n")
    
    validator_agent = create_validator_agent(home_directory)
    thread_id = "validation_session"
    
    # Convert implementation report to string for the validator - use model_dump_json
    impl_str = impl_report.model_dump_json(indent=2)
    
    # Stream validation agent execution
    print("✅ Validator Agent Working:")
    for chunk in validator_agent.stream(
        {
            "messages": [
                ("system", VALIDATOR_AGENT_PROMPT),
                ("user", f"Validate this implementation:\n\n{impl_str}\n\nUse git_diff and git_status to review changes, then validate code quality.")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }
    ):
        _print_agent_activity(chunk)
    
    validation_response = validator_agent.invoke(
        {
            "messages": [
                ("system", VALIDATOR_AGENT_PROMPT),
                ("user", f"Validate this implementation:\n\n{impl_str}\n\nUse git_diff and git_status to review changes, then validate code quality.")
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }
    )
    
    validation_report = extract_validation_report(validation_response)
    
    print("\n✓ Validation complete!")
    _print_validation_summary(validation_report)
    
    # Phase 4: Fix Loop (if needed)
    max_iterations = 3
    iteration = 0
    
    while not is_approved(validation_report) and iteration < max_iterations:
        iteration += 1
        print(f"\n[PHASE 4: FIX ITERATION {iteration}]")
        print("-" * 70)
        print("Implementation agent addressing validation feedback...\n")
        
        # Extract fix instructions
        fix_instructions = validation_report.fix_instructions
        if not fix_instructions:
            fix_instructions = validation_report.issues_found or ["Address the validation issues"]
        
        fix_request = "\n".join([f"- {instr}" for instr in fix_instructions])
        
        # Implementation agent fixes issues
        print("🔧 Implementation Agent Fixing Issues:")
        for chunk in implementation_agent.stream(
            {
                "messages": [
                    ("user", f"Fix these issues:\n\n{fix_request}\n\nAfter fixing, provide an updated implementation report.")
                ]
            },
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
        ):
            _print_agent_activity(chunk)
        
        impl_response = implementation_agent.invoke(
            {
                "messages": [
                    ("user", f"Fix these issues:\n\n{fix_request}\n\nAfter fixing, provide an updated implementation report.")
                ]
            },
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
        )
        
        impl_report = extract_implementation_report(impl_response)
        
        print("\n✓ Fixes applied!")
        _print_implementation_summary(impl_report)
        
        # Validator re-validates
        print("\n✅ Validator Agent Re-reviewing:")
        
        impl_str = impl_report.model_dump_json(indent=2)
        
        for chunk in validator_agent.stream(
            {
                "messages": [
                    ("user", f"Re-validate the updated implementation:\n\n{impl_str}\n\nCheck if the fixes resolved the issues.")
                ]
            },
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
        ):
            _print_agent_activity(chunk)
        
        validation_response = validator_agent.invoke(
            {
                "messages": [
                    ("user", f"Re-validate the updated implementation:\n\n{impl_str}\n\nCheck if the fixes resolved the issues.")
                ]
            },
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
        )
        
        validation_report = extract_validation_report(validation_response)
        
        print("\n✓ Re-validation complete!")
        _print_validation_summary(validation_report)
    
    # Final status
    print("\n" + "="*70)
    if is_approved(validation_report):
        print("✅ FINAL STATUS: APPROVED")
    elif iteration >= max_iterations:
        print("⚠️  FINAL STATUS: MAX ITERATIONS REACHED (needs manual review)")
    else:
        print("❓ FINAL STATUS: NEEDS REVIEW")
    print("="*70 + "\n")
    
    return {
        "plan": plan,
        "implementation": impl_report,
        "validation": validation_report,
        "status": "approved" if is_approved(validation_report) else "needs_review",
        "iterations": iteration
    }


def _print_agent_activity(chunk: dict):
    """Print agent activity from stream chunks."""
    # Show tool calls
    if "agent" in chunk:
        for message in chunk["agent"]["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    print(f"  🔧 Tool: {tool_name}", end='')
                    
                    # Show relevant args
                    if 'file_path' in tool_args:
                        print(f" → {tool_args['file_path']}", end='')
                    elif 'pattern' in tool_args:
                        print(f" → searching '{tool_args['pattern']}'", end='')
                    elif 'command' in tool_args:
                        cmd = tool_args['command'][:50]
                        print(f" → {cmd}{'...' if len(tool_args['command']) > 50 else ''}", end='')
                    print()
    
    # Show tool results
    if "tools" in chunk:
        for message in chunk["tools"]["messages"]:
            if hasattr(message, 'content'):
                content = str(message.content)
                # Show preview of tool output
                preview = content[:150].replace('\n', ' ')
                if len(content) > 150:
                    preview += "..."
                print(f"  ✓ Result: {preview}")


def _print_plan_summary(plan: PlanOutput):
    """Print a summary of the plan."""
    print()
    print(f"Analysis: {plan.analysis}")
    
    if plan.context:
        print(f"\nContext: {plan.context}")
    
    if plan.files_to_create:
        print(f"\n📝 Files to create: {len(plan.files_to_create)}")
        for f in plan.files_to_create[:5]:
            purpose_preview = f.purpose[:60] if len(f.purpose) > 60 else f.purpose
            print(f"  + {f.path}: {purpose_preview}")
        if len(plan.files_to_create) > 5:
            print(f"  ... and {len(plan.files_to_create) - 5} more")
    
    if plan.files_to_modify:
        print(f"\n✏️  Files to modify: {len(plan.files_to_modify)}")
        for f in plan.files_to_modify[:5]:
            purpose_preview = f.purpose[:60] if len(f.purpose) > 60 else f.purpose
            print(f"  ~ {f.path}: {purpose_preview}")
        if len(plan.files_to_modify) > 5:
            print(f"  ... and {len(plan.files_to_modify) - 5} more")
    
    if plan.steps:
        print(f"\n📋 Total steps: {len(plan.steps)}")
        
    if plan.considerations:
        print(f"\n⚠️  Considerations: {len(plan.considerations)}")
        for c in plan.considerations[:3]:
            print(f"  - {c}")
        if len(plan.considerations) > 3:
            print(f"  ... and {len(plan.considerations) - 3} more")



def _print_implementation_summary(report: ImplementationReport):
    """Print a summary of the implementation report."""
    print()
    print(f"Status: {report.status}")
    
    if report.files_created:
        print(f"\n📝 Created: {', '.join(report.files_created)}")
    
    if report.files_modified:
        print(f"✏️  Modified: {', '.join(report.files_modified)}")
    
    if report.linting_results:
        print("\n📊 Linting scores:")
        for file, result in list(report.linting_results.items())[:5]:
            issues_str = f" ({len(result.issues)} issues)" if result.issues else " ✓"
            syntax_str = "✓" if result.syntax_valid else "✗ SYNTAX ERROR"
            print(f"  {file}: {result.score}/10 [{syntax_str}]{issues_str}")
    
    if report.summary:
        print(f"\n💬 {report.summary}")
    
    if report.issues_encountered:
        print(f"\n⚠️  Issues: {len(report.issues_encountered)}")
        for issue in report.issues_encountered[:3]:
            print(f"  - {issue}")



def _print_validation_summary(report: ValidationReport):
    """Print a summary of the validation report."""
    print()
    approval_icon = "✅" if report.approval else "❌"
    print(f"Status: {report.status} {approval_icon}")
    print(f"Overall quality: {report.overall_quality}")
    
    if report.changes_summary:
        print(f"\n📝 Changes: {report.changes_summary}")
    
    if report.files_reviewed:
        print(f"\n📋 Files reviewed: {len(report.files_reviewed)}")
        for f in report.files_reviewed[:5]:
            print(f"  - {f}")
    
    if report.quality_assessment:
        print(f"\n📊 Quality assessment:")
        for file, assessment in list(report.quality_assessment.items())[:5]:
            syntax_str = "✓" if assessment.syntax_valid else "✗ SYNTAX ERROR"
            print(f"  {file}: {assessment.score}/10 [{syntax_str}]")
    
    if report.issues_found:
        print(f"\n⚠️  Issues found: {len(report.issues_found)}")
        for issue in report.issues_found[:5]:
            print(f"  - {issue}")
        if len(report.issues_found) > 5:
            print(f"  ... and {len(report.issues_found) - 5} more")
    
    if report.fix_instructions:
        print(f"\n🔧 Fixes needed:")
        for fix in report.fix_instructions[:5]:
            print(f"  - {fix}")
        if len(report.fix_instructions) > 5:
            print(f"  ... and {len(report.fix_instructions) - 5} more")

