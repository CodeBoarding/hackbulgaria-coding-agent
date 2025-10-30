# HackBulgaria Coding Agent - Implementation Plan

## Project Overview
Building a coding agent using LangChain and Google Gemini with a ReACT (Reasoning and Acting) architecture. The project will follow an iterative, minimal implementation approach.

## Phase 1: Minimal ReACT Coding Agent ✅ COMPLETE

### Goal
Create a basic ReACT agent that can read and write files using Google Gemini as the LLM.

### Core Components

#### 1. Tools (Minimal Set)
- **Read File Tool**: Reads content from a specified file path
  - Input: file path (string)
  - Output: file content (string) with line numbering upfront, or error message
  - Error handling: file not found, permission errors

- **Write File Tool**: Writes content to a specified file path
  - Input: file path (string), new content (string), line range in which the new content will be placed
  - Output: success confirmation or error message
  - Error handling: permission errors, directory creation if needed

#### 2. ReACT Agent
- Use LangChain's ReACT agent implementation
- Integrate Google Gemini via langchain-google-genai
- Agent should be able to:
  - Reason about what actions to take
  - Use the read/write tools appropriately
  - Provide thought process in responses

#### 3. Configuration
- Environment variables for API keys (GOOGLE_API_KEY), use .env for this
- Basic agent configuration (model name, temperature, etc.)

### Implementation Steps

1. **Setup Environment** ✅
   - Initialize Python 3.12 venv with uv
   - Install dependencies (langchain, langchain-google-genai, pylint, astroid)
   - Configure Git repository

2. **Create Tool Implementations** ✅
   - Implement read_file tool as LangChain tool
   - Implement write_file tool as LangChain tool
   - Add basic validation and error handling
   - Add home directory support for sandboxing

3. **Initialize Gemini LLM** ✅
   - Configure Google Gemini model
   - Set up API key management
   - Test basic LLM functionality

4. **Build ReACT Agent** ✅
   - Create ReACT agent with Gemini + tools (use the default from langchain/langgraph)
   - Configure agent parameters
   - Add prompt engineering for coding tasks

5. **Create Main Interface** ✅
   - Simple CLI or Python script to interact with agent
   - Accept user prompts
   - Display agent reasoning and actions
   - Format output for better readability

### Success Criteria ✅
- Agent can successfully read files from the file system ✅
- Agent can successfully write files to the file system ✅
- Agent demonstrates ReACT pattern (thought → action → observation) ✅
- Agent can complete simple coding tasks (e.g., "read config.py and create a summary in summary.txt") ✅
- Agent supports home directory for sandboxed operations ✅
- Clean formatted output ✅

---

## Phase 2: Conversation Memory ✅ COMPLETE

### Goal
Add short-term memory to the agent so it can remember previous messages in the conversation and maintain context across multiple exchanges.

### Problem Statement
Currently, if the agent creates a plan and asks for confirmation, when the user replies "yes", the agent has no memory of what it was asking about. We need conversation history.

### Minimal Implementation

#### 1. Use LangChain's Built-in Memory
- Use `ConversationBufferMemory` from LangChain (simplest option)
- Stores all messages in the current session
- No persistence needed (memory clears when program exits)

#### 2. Integration Points
- Modify `create_coding_agent()` in `react_agent.py`
- Pass memory to the agent via checkpointer
- Use LangGraph's `MemorySaver` for state persistence during session

#### 3. Implementation Steps

1. **Add Memory to Agent** ✅
   - Import `MemorySaver` from langgraph.checkpoint.memory
   - Create memory checkpointer
   - Pass checkpointer to `create_react_agent()`

2. **Update Main Loop** ✅
   - Maintain a `thread_id` for the conversation session
   - Pass `thread_id` in config when invoking agent
   - All messages in same session will share memory

3. **Test Memory** ✅
   - Agent asks question → user confirms → agent remembers context

### Code Changes Required
```python
# In react_agent.py
from langgraph.checkpoint.memory import MemorySaver

def create_coding_agent(home_directory=None):
    llm = ChatGoogleGenerativeAI(...)
    tools = [read_file_func, write_file_func]
    
    # Add memory
    memory = MemorySaver()
    agent = create_react_agent(llm, tools, checkpointer=memory)
    return agent

# In main.py
thread_id = "default_session"  # Single session for CLI
result = agent.invoke(
    {"messages": [("user", user_input)]},
    config={"configurable": {"thread_id": thread_id}}
)
```

### Success Criteria ✅
- Agent remembers previous messages in the conversation ✅
- User can confirm/deny without re-explaining context ✅
- Memory persists throughout CLI session ✅
- Memory clears when program restarts (expected behavior) ✅

### Future Enhancements (Post-Phase 2)
- Persistent memory (save to disk/database)
- Summary-based memory (for long conversations)
- Multiple conversation threads
- Memory trimming (keep last N messages)

---

## Phase 3: Pylint Code Validation ✅ COMPLETE

### Goal
Add pylint validation as a tool so the agent can check if the Python code it generates is properly linted and follows best practices.

### Problem Statement
The agent can create and modify Python files, but has no way to validate that the code it generates:
- Has no syntax errors
- Follows Python best practices
- Has no linting issues (unused imports, undefined variables, etc.)

Adding pylint as a tool allows the agent to self-validate its code generation.

### Minimal Implementation

#### 1. Create Pylint Tool
- New tool: `validate_code` or `lint_file`
- Input: file path to Python file
- Output: Linting results (errors, warnings, info)
- Uses pylint's programmatic API (already installed)

#### 2. Tool Capabilities
- Run pylint on a specific Python file
- Return structured output: score, errors, warnings
- Format output to be readable for the LLM
- Allow agent to fix issues based on lint results

#### 3. Integration Points
- Add new tool to `src/tools/` directory
- Register tool with agent in `react_agent.py`
- Agent can use tool as part of its workflow

### Implementation Steps

1. **Create Lint Tool** ✅
   - Create `src/tools/lint_tools.py`
   - Implement `lint_file` tool using pylint API
   - Parse pylint output into structured format
   - Handle errors gracefully

2. **Integrate with Agent** ✅
   - Import lint tool in `react_agent.py`
   - Add to tools list
   - Agent now has access to validation

3. **Add System Prompt** ✅
   - Create comprehensive system prompt
   - Instructs agent to always validate code
   - Defines best practices and workflow

4. **Test Integration** ✅
   - Agent creates Python file
   - Agent runs lint on file
   - Agent sees issues and can fix them

### Proposed Tool Interface

```python
@tool
def lint_file(file_path: str) -> str:
    """Run pylint on a Python file and return linting results.
    
    Args:
        file_path: Path to Python file to lint
        
    Returns:
        Formatted linting results with score, errors, and warnings
    """
    # Run pylint
    # Parse results
    # Return formatted output
```

### Expected Output Format
```
Pylint Score: 8.5/10

Errors:
  Line 5: undefined-variable - Undefined variable 'x'
  
Warnings:
  Line 10: unused-import - Unused import 'sys'
  Line 15: line-too-long - Line too long (120/100)

Info:
  No style issues found
```

### Success Criteria ✅
- Tool can successfully run pylint on Python files ✅
- Returns clear, actionable feedback ✅
- Agent can use tool to validate its own code ✅
- Agent can iterate: create → lint → fix → lint again ✅
- Works with home directory restrictions ✅
- System prompt guides agent to use linting automatically ✅

### Use Case Example
```
You: Create a Python script with a function to calculate factorial
Agent: [Creates file] 
Agent: [Uses lint_file tool to validate]
Agent: "I've created factorial.py with a pylint score of 9.5/10"
```

### Future Enhancements (Post-Phase 3)
- Auto-fix mode using pylint's --fix option
- Configurable pylint rules (.pylintrc)
- Code formatting with black/autopep8
- Type checking with mypy
- Security scanning with bandit

### Future Enhancements (Post-Phase 1)
- Memory and conversation history → Phase 2 ✅
- Code validation with pylint → Phase 3 ✅
- Multi-agent system → Phase 4 🔄
- Additional tools (search, execute code, git operations)
- Multi-file operations
- Code analysis tools (using astroid)
- Improved error handling and recovery
- Structured output and logging

## Project Structure
```
hb-coding-agent/
├── .venv/                  # Virtual environment
├── .gitignore
├── README.md
├── requirements.txt
├── plan.md                 # This file
├── .env                    # API keys (not committed)
├── src/
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_tools.py   # Read/write file tools
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_agent.py  # ReACT agent implementation
│   ├── config.py           # Configuration management
│   └── main.py             # Entry point
```

## Next Immediate Steps
1. ~~Create project structure (src/, tests/ directories)~~ ✅
2. ~~Implement file tools (read_file, write_file)~~ ✅
3. ~~Set up Gemini LLM configuration~~ ✅
4. ~~Build ReACT agent~~ ✅
5. ~~Create simple CLI interface~~ ✅
6. ~~Add conversation memory (Phase 2)~~ ✅
7. ~~Add pylint validation tool (Phase 3)~~ ✅
8. Implement multi-agent system (Phase 4) 🔄

---

## Phase 4: Multi-Agent System 🔄 IN PROGRESS

### Goal
Transform the single ReACT agent into a collaborative multi-agent system where specialized agents work together to solve coding tasks. This creates a more robust system with separation of concerns: planning, implementation, and validation.

### Overview
Instead of one agent doing everything, we'll have three specialized agents that communicate and collaborate:

1. **Planning Agent (Readonly)**: Analyzes the problem, explores the codebase, creates execution plan
2. **Implementation Agent (Read/Write)**: Executes the plan, modifies files, uses linting
3. **Validator Agent (Readonly + Git)**: Validates changes using git diff and linting

### Architecture

#### Agent Communication Flow
```
User Request
    ↓
Planning Agent
    → Explores codebase (read files, grep search, bash commands)
    → Analyzes requirements
    → Creates execution plan (structured format)
    ↓
Implementation Agent
    → Receives execution plan
    → Implements changes (create/edit files)
    → Runs linting on changes
    → Reports implementation status
    ↓
Validator Agent
    → Reviews changes (git diff)
    → Validates code quality (linting, AST)
    → Provides approval or requests fixes
    ↓
[If fixes needed: Implementation Agent → Validator Agent loop]
    ↓
Final Result to User
```

### Agent Specifications

#### 1. Planning Agent
**Role**: Understand requirements and create actionable plan

**Tools (Read-only)**:
- `read_file`: Read existing files
- `run_bash_command`: Explore directory structure, search files
- `grep_search`: NEW - Multi-file text search tool

**Responsibilities**:
- Analyze user request
- Explore codebase to understand structure
- Search for relevant files and code patterns
- Create detailed execution plan with:
  - Files to create/modify
  - Changes to make
  - Order of operations
  - Dependencies and considerations

**Output Format**: Structured plan (JSON or Markdown)
```json
{
  "analysis": "Summary of the problem",
  "files_to_modify": ["file1.py", "file2.py"],
  "files_to_create": ["new_file.py"],
  "steps": [
    {"action": "create", "file": "new_file.py", "description": "..."},
    {"action": "modify", "file": "file1.py", "description": "..."}
  ],
  "considerations": ["edge case 1", "dependency on X"]
}
```

#### 2. Implementation Agent
**Role**: Execute the plan and make code changes

**Tools (Read/Write)**:
- `read_file`: Read files to understand context
- `write_file`: Create and modify files
- `lint_file`: Validate Python code quality
- `run_bash_command`: Limited bash operations

**Responsibilities**:
- Parse execution plan from Planning Agent
- Implement each step in order
- Run linting after each Python file change
- Fix linting issues automatically
- Report implementation progress

**Input**: Execution plan from Planning Agent
**Output**: Implementation report with:
- Files created/modified
- Linting scores
- Any issues encountered
- Status (success/partial/failed)

#### 3. Validator Agent
**Role**: Validate implementation quality and correctness

**Tools (Read-only + Git)**:
- `git_diff`: NEW - Show changes made (git diff)
- `git_status`: NEW - Show file change status
- `lint_file`: Validate code quality
- `read_file`: Review final state of files

**Responsibilities**:
- Review git diff to see all changes
- Validate code quality (linting, AST parsing)
- Check that implementation matches plan
- Provide approval or request specific fixes
- Generate validation report

**Output**: Validation report with:
- Changes summary (from git diff)
- Code quality assessment
- Issues found (if any)
- Approval status (approved/needs-fixes)
- Specific fixes required

### New Tools to Implement

#### 1. grep_search Tool
**Purpose**: Multi-file text search across codebase

```python
@tool
def grep_search(pattern: str, file_pattern: str = "*.py", case_sensitive: bool = False) -> str:
    """Search for text pattern across multiple files.
    
    Args:
        pattern: Text or regex pattern to search for
        file_pattern: File glob pattern (e.g., "*.py", "src/**/*.py")
        case_sensitive: Whether search is case-sensitive
        
    Returns:
        Formatted search results with file paths and line numbers
    """
```

**Use Cases**:
- Find all usages of a function
- Search for TODO comments
- Find import statements
- Locate class definitions

#### 2. git_diff Tool
**Purpose**: Show changes made to files

```python
@tool
def git_diff(file_path: str = "") -> str:
    """Show git diff of changes.
    
    Args:
        file_path: Optional specific file to diff (empty = all changes)
        
    Returns:
        Git diff output showing changes
    """
```

#### 3. git_status Tool
**Purpose**: Show status of working directory

```python
@tool
def git_status() -> str:
    """Show git status of working directory.
    
    Returns:
        List of modified, created, deleted files
    """
```

### Multi-Agent Orchestration

#### Coordinator/Orchestrator
A simple orchestrator function that:
1. Takes user request
2. Invokes Planning Agent → gets plan
3. Invokes Implementation Agent with plan → gets implementation report
4. Invokes Validator Agent → gets validation report
5. If validation fails: loop (Implementation Agent → Validator Agent)
6. Returns final result to user

**Implementation Approach**: Simple sequential function (not another agent)

```python
def orchestrate_multi_agent(user_request: str, home_directory: str = None):
    """Orchestrate multiple agents to handle a coding request."""
    
    # Phase 1: Planning
    planning_agent = create_planning_agent(home_directory)
    plan = planning_agent.invoke({"messages": [("user", user_request)]})
    
    # Phase 2: Implementation
    implementation_agent = create_implementation_agent(home_directory)
    impl_report = implementation_agent.invoke({
        "messages": [("user", f"Execute this plan:\n{plan}")]
    })
    
    # Phase 3: Validation
    validator_agent = create_validator_agent(home_directory)
    validation = validator_agent.invoke({
        "messages": [("user", f"Validate this implementation:\n{impl_report}")]
    })
    
    # Phase 4: Fix loop (if needed)
    max_iterations = 3
    iteration = 0
    while not is_approved(validation) and iteration < max_iterations:
        fix_request = extract_fixes(validation)
        impl_report = implementation_agent.invoke({
            "messages": [("user", f"Fix these issues:\n{fix_request}")]
        })
        validation = validator_agent.invoke({
            "messages": [("user", f"Re-validate:\n{impl_report}")]
        })
        iteration += 1
    
    return {
        "plan": plan,
        "implementation": impl_report,
        "validation": validation,
        "status": "approved" if is_approved(validation) else "needs_review"
    }
```

### File Structure for Phase 4

```
src/
├── tools/
│   ├── file_tools.py      # Existing
│   ├── bash_tools.py      # Existing
│   ├── lint_tools.py      # Existing
│   ├── git_tools.py       # NEW - git diff, git status
│   └── search_tools.py    # NEW - grep_search
├── agent/
│   ├── react_agent.py     # Existing (might refactor)
│   ├── planning_agent.py  # NEW
│   ├── implementation_agent.py  # NEW
│   ├── validator_agent.py # NEW
│   └── orchestrator.py    # NEW - coordinates agents
├── main.py                # Updated to use orchestrator
└── config.py              # Existing
```

### Implementation Steps (Minimal)

#### Step 1: Create New Tools
1. **git_tools.py**: Implement git_diff and git_status
   - Use subprocess to run git commands
   - Parse and format output
   - Handle errors (no git repo, no changes, etc.)

2. **search_tools.py**: Implement grep_search
   - Use subprocess to run grep or native Python search
   - Format results with file paths and line numbers
   - Support glob patterns for file filtering

#### Step 2: Create Specialized Agents
1. **planning_agent.py**: 
   - Create agent with readonly tools only
   - System prompt: "You are a planning agent..."
   - Tools: read_file, run_bash_command, grep_search

2. **implementation_agent.py**:
   - Create agent with read/write tools
   - System prompt: "You are an implementation agent..."
   - Tools: read_file, write_file, lint_file, run_bash_command

3. **validator_agent.py**:
   - Create agent with validation tools
   - System prompt: "You are a validator agent..."
   - Tools: git_diff, git_status, lint_file, read_file

#### Step 3: Create Orchestrator
1. **orchestrator.py**:
   - Simple function-based orchestration (not agent-based)
   - Sequential execution: Planning → Implementation → Validation
   - Simple fix loop with max iterations
   - Structured output format

#### Step 4: Update Main CLI
1. **main.py**:
   - Add flag for multi-agent mode: `--multi-agent`
   - When enabled, use orchestrator instead of single agent
   - Display progress for each phase
   - Show intermediate results (plan, implementation, validation)

### System Prompts

#### Planning Agent Prompt
```
You are an expert planning agent. Your role is to analyze coding requests and create detailed execution plans.

You have READ-ONLY access to the codebase. Use your tools to:
- Explore directory structure
- Read existing files
- Search for patterns across files
- Understand current code organization

Your output should be a structured plan with:
1. Analysis: Summary of the problem
2. Files to create: List with descriptions
3. Files to modify: List with descriptions
4. Step-by-step actions: Ordered list of what to do
5. Considerations: Edge cases, dependencies, risks

Be thorough and specific. The implementation agent will follow your plan exactly.
```

#### Implementation Agent Prompt
```
You are an expert implementation agent. Your role is to execute coding plans.

You will receive a plan from the planning agent. Follow it step by step:
1. Create or modify files as specified
2. After each Python file change, run lint_file
3. Fix any linting issues immediately
4. Report progress and results

Be precise and careful. Aim for clean, well-tested code with pylint scores of 8.0+.
```

#### Validator Agent Prompt
```
You are an expert validation agent. Your role is to review and validate code changes.

Use your tools to:
1. Check git diff to see all changes
2. Validate code quality with linting
3. Verify implementation matches the plan
4. Check for edge cases and issues

Provide a validation report with:
- Summary of changes
- Code quality assessment
- Issues found (be specific)
- Approval status (approved/needs-fixes)
- If fixes needed: specific instructions

Be thorough but fair. Focus on correctness and quality.
```

### Communication Format

Agents communicate via **structured messages** in their shared memory/context:

```python
# Planning Agent Output
{
    "type": "plan",
    "analysis": "User wants to create a REST API endpoint...",
    "files_to_create": [
        {"path": "api/users.py", "purpose": "User endpoint handlers"}
    ],
    "files_to_modify": [
        {"path": "api/__init__.py", "purpose": "Register new routes"}
    ],
    "steps": [
        {"seq": 1, "action": "create", "file": "api/users.py", "details": "..."},
        {"seq": 2, "action": "modify", "file": "api/__init__.py", "details": "..."}
    ]
}

# Implementation Agent Output
{
    "type": "implementation_report",
    "status": "success",
    "files_created": ["api/users.py"],
    "files_modified": ["api/__init__.py"],
    "linting_results": {
        "api/users.py": {"score": 9.5, "issues": []},
        "api/__init__.py": {"score": 10.0, "issues": []}
    }
}

# Validator Agent Output
{
    "type": "validation_report",
    "status": "approved",  # or "needs_fixes"
    "changes_summary": "Created users.py with GET/POST handlers...",
    "quality_score": 9.5,
    "issues": [],
    "approval": true,
    "fix_instructions": []  # populated if approval is false
}
```

### Minimal Implementation Checklist

- [ ] Create `src/tools/git_tools.py` with git_diff and git_status
- [ ] Create `src/tools/search_tools.py` with grep_search
- [ ] Create `src/agent/planning_agent.py` with readonly tools
- [ ] Create `src/agent/implementation_agent.py` with read/write tools
- [ ] Create `src/agent/validator_agent.py` with validation tools
- [ ] Create `src/agent/orchestrator.py` with sequential coordination
- [ ] Update `src/main.py` to support `--multi-agent` flag
- [ ] Test with simple task: "Create a hello world function"
- [ ] Test with complex task: "Add REST endpoint for users"

### Success Criteria

✅ **Planning Agent**:
- Can explore codebase with readonly tools
- Produces structured, actionable plans
- Uses grep_search to find relevant code

✅ **Implementation Agent**:
- Follows plans from planning agent
- Creates/modifies files correctly
- Runs linting automatically
- Fixes issues iteratively

✅ **Validator Agent**:
- Reviews changes with git diff
- Validates code quality
- Provides clear feedback
- Approves or requests specific fixes

✅ **Orchestration**:
- Sequential flow works: Planning → Implementation → Validation
- Fix loop works: Implementation ↔ Validator (max 3 iterations)
- User sees progress for each phase
- Final result includes all phase outputs

✅ **End-to-End**:
- User gives request → system produces validated implementation
- Changes are committed to git (or ready to commit)
- All Python files pass linting
- System provides comprehensive report

### Example Usage

```bash
# Single agent mode (existing)
python src/main.py --home ./test-project
You: Create a factorial function

# Multi-agent mode (new)
python src/main.py --home ./test-project --multi-agent
You: Create a factorial function

# Output:
# [PLANNING] Analyzing request...
# [PLANNING] Creating execution plan...
# Plan: Create factorial.py with factorial function and tests
# 
# [IMPLEMENTATION] Executing plan...
# [IMPLEMENTATION] Created factorial.py
# [IMPLEMENTATION] Linting: 9.5/10
# 
# [VALIDATION] Reviewing changes...
# [VALIDATION] Git diff: +25 lines in factorial.py
# [VALIDATION] Code quality: Excellent
# [VALIDATION] ✅ APPROVED
#
# Final Result: Successfully created factorial function with validation
```

### Technical Considerations

1. **Agent Independence**: Each agent is an independent ReACT agent with its own tools and prompt
2. **No Shared State**: Agents communicate via messages/outputs, not shared memory
3. **Sequential Execution**: Simple coordinator function, not parallel (easier to implement)
4. **Error Handling**: Each agent can fail independently; orchestrator handles failures
5. **Iteration Limit**: Max 3 fix iterations to prevent infinite loops
6. **Git Requirements**: Assumes working directory is a git repo (or initialize one)

### Future Enhancements (Post-Phase 4)

- Parallel agent execution where possible
- Human-in-the-loop approval points
- More sophisticated agent communication (message bus)
- Agent specialization (testing agent, documentation agent)
- Learning from validation feedback
- Cost tracking per agent
- Agent performance metrics

````
