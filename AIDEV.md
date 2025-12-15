# Project MUTT - Development Context

## High Level Goal
Modernize syslog/SNMP trap handling using Python.

## Current Architecture
- `main.py`: Entry point.
- `listener.py`: UDP socket handler.

## Active Task
- Implementing the parser logic for SNMP v3 packets.

## Recent Decisions (The "Log")
- [2025-12-14] Gemini suggested using `pysnmp` over `easysnmp` due to compilation issues.
- [2025-12-14] Claude refactored the logging class to use JSON output.

## Outstanding Questions/Bugs
- The listener times out after 60s (Needs fix).
