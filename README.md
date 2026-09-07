# AI Development Orchestrator

An autonomous, multi-phase software engineering desktop orchestration system for Windows that coordinates specialized AI applications to plan, implement, review, and finalize software projects.

---

## Architecture & Workflow

The system manages a robust state machine separating **Planner**, **Implementer**, and **Reviewer** responsibilities:

```
User Requirements
        ↓
Claude Planner
        ↓
Structured Development Plan (JSON)
        ↓
Antigravity Implementer
        ↓
Implementation / Testing (Workspace & Reports)
        ↓
Claude Reviewer
        ↓
Decision Engine
   ↙       ↓       ↘
Retry    Next      Stop
                     ↓
                 FINALIZING
                     ↓
            Final Project Handoff
           (final_project_handoff.md)
                     ↓
                 COMPLETED
```

### End-to-End Orchestration Loop

1. **User Requirements**: The user provides a project name and high-level requirements via the desktop GUI or API.
2. **Claude Planner**: The programmatically generated planning prompt is sent to Claude Desktop via UI automation. Claude returns a structured multi-phase plan adhering to a strict JSON schema.
3. **Structured Validation**: The plan is extracted and validated against strict schema rules (task IDs, objectives, instructions, file boundaries, and acceptance criteria).
4. **Antigravity Implementer**: The orchestrator brings Antigravity to the foreground, focuses the chat input box (using layout detection for new vs. existing chats), and dispatches task instructions. Antigravity develops the code inside the isolated workspace and writes a markdown implementation report.
5. **Claude Reviewer**: The report and project state are dispatched to Claude Desktop for independent technical review.
6. **Decision Engine**:
   - **`APPROVED + NEXT_PHASE`**: Advances to the next development phase.
   - **`CORRECTION_NEEDED`**: Packages reviewer feedback into a targeted retry prompt and triggers a correction attempt (up to maximum retries).
   - **`BLOCKED`**: Safely stops execution and reports blocking issues to the dashboard.
   - **`APPROVED + STOP`**: Triggers the **`FINALIZING`** workflow state.
7. **Final Project Handoff**: Antigravity generates a user-facing `final_project_handoff.md` report summarizing what was built, project structure, setup, run instructions, and testing commands (with an automatic fallback generator if needed).
8. **Completion**: The GUI displays the live status, enables viewing the final handoff report, and provides a direct shortcut to open the project workspace in Windows Explorer.

---

## Core Features

- **Multi-Phase Orchestration**: Coordinates complex projects across multiple incremental milestones.
- **Claude Desktop Planner & Reviewer**: Automated window discovery, prompt dispatch, and response capture.
- **Antigravity Implementer**: Layout-aware UI automation targeting middle (new chat) or bottom (existing chat) inputs with candidate scoring and foreground verification.
- **Stateful Workflow Engine**: Managed state transitions (`SETUP` -> `PLANNER` -> `WORKER` -> `IMPLEMENTATION` -> `REPORT` -> `REVIEWER` -> `DECISION` -> `FINALIZING` -> `COMPLETED`).
- **Structured JSON Validation & Normalization**: Tolerant extraction handling markdown fences, control characters, and schema enforcement.
- **Retry & Feedback Loops**: Closed-loop defect correction feeding reviewer issues back into subsequent implementation attempts.
- **Audit & Persistence**: SQLite database recording all phase iterations, reviewer assessments, and execution histories.
- **Desktop GUI Dashboard**: Built with Tkinter, featuring real-time stage progress indicators, color-coded activity logs, and modal report inspection.
- **Automated Project Handoff**: Dedicated finalization phase providing clear instructions on how to run and test the generated project.

---

## Prerequisites

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.10, 3.11, 3.12, or 3.13
- **Claude Desktop Application**: Installed and accessible on the Windows desktop
- **Antigravity Application**: Installed and accessible on the Windows desktop
- **Display**: Active Windows interactive desktop session (UI automation requires active screen rendering)

---

## CRITICAL OPERATING INSTRUCTION

> [!IMPORTANT]
> **Before starting the AI Development Orchestrator, ensure that Claude Desktop is open and that the target project workspace/directory is already opened in Antigravity. Pre-opening both applications and loading the target workspace helps ensure uninterrupted desktop automation and reliable end-to-end orchestration.**

---

## Installation

1. **Clone the Repository**:
   ```cmd
   git clone https://github.com/omkar-1849/AI-Development-Orchestrator.git
   cd AI-Development-Orchestrator
   ```

2. **Create and Activate a Virtual Environment**:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

---

## Running the Application

Launch the desktop graphical interface:

```cmd
python main.py
```

### GUI Usage:
1. Enter a **Project Name** (e.g. `TaskManagerAPI`).
2. Provide detailed **Project Requirements** in the prompt area.
3. Click **Start Project**.
4. The dashboard will display live progress across all pipeline stages, streaming log events, and phase counters.
5. Once complete, click **View Final Report** to inspect the handoff documentation or **Open Folder** to view generated source files.

---

## Running Tests

Execute the full automated test suite:

```cmd
python -m unittest discover tests -v
```

All unit and integration tests use mocks for UI automation and external applications, allowing the entire suite to run offline without disturbing open desktop windows.

---

## Environment Configuration

The orchestrator includes automatic application discovery for standard Windows installation paths. If your applications are installed in custom directories, you can configure optional environment variable overrides:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `CLAUDE_APP_PATH` | Explicit path to Claude Desktop executable | `C:\Users\username\AppData\Local\Programs\Claude\Claude.exe` |
| `ANTIGRAVITY_APP_PATH` | Explicit path to Antigravity executable | `C:\Users\username\AppData\Local\Programs\Antigravity\Antigravity.exe` |
| `APP_DISCOVERY_TIMEOUT` | Timeout in seconds when searching for windows (default: `5.0`) | `10.0` |
| `APP_STARTUP_TIMEOUT` | Timeout in seconds waiting for app launch (default: `15.0`) | `20.0` |
| `ORCHESTRATOR_HANDOFF_TIMEOUT` | Timeout in seconds waiting for handoff report (default: `180.0`) | `120.0` |

---

## Final Project Handoff

When all planned phases are completed and the reviewer returns:
```json
{
  "decision": "APPROVED",
  "next_action": "STOP"
}
```

The system enters the **`FINALIZING`** state:
1. Antigravity is instructed to inspect the generated codebase and create `final_project_handoff.md` in the project root.
2. The report specifies:
   - What was built and key features implemented
   - Entry points and important project files
   - Environment setup instructions
   - Step-by-step commands to run the application
   - Commands to execute tests
3. If Antigravity encounters an issue generating the report, the orchestrator automatically compiles a safe fallback handoff report from pipeline metadata, ensuring the user always receives actionable instructions.
4. The workflow transitions to **`COMPLETED`**.

---

## License

This project is licensed under the MIT License.
