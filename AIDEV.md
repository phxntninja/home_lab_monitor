# Homelab Monitoring Dashboard - Project Summary

## Project Overview
This project aims to create a comprehensive monitoring dashboard for my home lab environment. It will collect data from various devices and services, visualize it in a user-friendly interface, and provide alerts for critical events.

## Requirements
*   **Data Collection:** Collect metrics from servers, network devices, and virtual machines.
*   **Visualization:** Display data in real-time dashboards with customizable views.
*   **Alerting:** Configure alerts for critical events, such as high CPU usage or network outages.
*   **Storage:** Store historical data for trend analysis and reporting.
*   **Accessibility:** Access the dashboard from any device with a web browser.

## Technology Stack
*   **Data Collection:** Python, SNMP, Telegraf
*   **Backend:** Python (Flask), InfluxDB
*   **Frontend:** JavaScript (React), Grafana
*   **Operating System:** Ubuntu Server

## Phase 1: UDP SNMP Listener
*   Implement a UDP SNMP listener in Python to collect data from network devices.
*   Parse SNMP data and store it in InfluxDB.
*   Create basic Grafana dashboards to visualize the collected data.

## Architecture Context

We are adopting a Hybrid Monolith architecture.

*   **Directory Structure:** Separate `config/` and `logs/` folders. Code lives in `app/`.
*   **Modules:** Use `app/monitors/` for the background threads.
*   **State:** A flat dictionary protected by a context manager lock.
*   **Concurrency:** Daemon threads started from `main.py`.
*   **Output:** JSON Lines for logs in the `logs/` directory.
*   **Config:** `snmp_credentials.yaml` and `.env` live in `config/`.

## Active Decisions

*   **Hybrid Monolith:** The application will follow a hybrid monolith architecture for simplified deployment and management.
*   **Directory Structure:** The project will be organized with separate `config/`, `logs/`, and `app/` directories for clarity and maintainability.
*   **Modules:** Background threads for monitoring will be placed in the `app/monitors/` directory.
*   **State:** Application state will be managed using a flat dictionary protected by a context manager lock to ensure thread safety.
*   **Concurrency:** Daemon threads will be utilized and started from `main.py` for concurrent execution of monitoring tasks.
*   **Output:** Logs will be written in JSON Lines format to the `logs/` directory for structured and easily parsable logging.
*   **Config:** Configuration files, including `snmp_credentials.yaml` and `.env`, will reside in the `config/` directory for centralized configuration management.
## Status: PAUSED (Dec 14)
- Syslog Listener: COMPLETE (Verified)
- StateManager: COMPLETE
- Next: SNMP Listener
