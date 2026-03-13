# Py-Coding-Agent Design Document

## Goal

Build a local Python coding agent inspired by pi-mono that can:

- Execute tasks in a sandbox
- Dynamically create and run Python tools
- Install Python packages as needed
- Interface with an LLM (Ollama)

## Architecture

User CLI → Agent → Tools → Runtime Environment

**Runtime Environment**

- Docker container
- Workspace directory
- Dynamic tools folder
- uv-based package management

## V1 Scope

- CLI interface
- Base toolset (read/write/edit files, shell, uv install)
- Dynamic tool creation and loading
- Docker sandbox for safe execution
- Ollama LLM integration

## V2 Ideas

- Multi-agent pods (planner, coder, tester)
- Tool schema validation and registry
- Memory indexing for tools
- Automatic tool testing