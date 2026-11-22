# ResearchHub MBA — Antigravity workspace entry point

This file is automatically discovered by Antigravity when the **repository root** is opened as the workspace.

@[ResearchHub engineering and governance rules](agent.md)

The project product and architecture specification is @gdd.md. **Read it before planning, modifying, or reviewing code.**

## Mandatory execution gates
1. Work only within the explicitly assigned, approved phase. No phase assignment means **do not begin coding**.
2. Treat `gdd.md` as the product and architecture baseline. If requested work conflicts with it, report the conflict and seek Project Owner/PM approval; do not silently change the architecture.
3. Never commit research documents, application data, SQLite databases, backups, `.env` files, tokens, or credentials.
4. Do not push directly to `main`; use a `phase/<number>-<slug>` branch and open a Pull Request when authorized to implement a phase.
5. Before marking a phase complete, produce tests, run validation, and provide a concise handoff report with the PR URL and commit SHA. The PM reviews the PR before merging.

**Status (2026-11-22):** governance draft for approval; this file does not authorize starting implementation.
