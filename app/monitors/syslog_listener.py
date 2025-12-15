#!/usr/bin/env python3
"""Syslog UDP listener for collecting log messages."""

import socket
import re
from datetime import datetime


# Syslog severity levels
SEVERITY_NAMES = {
    0: "Emergency",
    1: "Alert",
    2: "Critical",
    3: "Error",
    4: "Warning",
    5: "Notice",
    6: "Informational",
    7: "Debug"
}

# High severity levels that should trigger alerts
HIGH_SEVERITY = [0, 1, 2, 3]  # Emergency, Alert, Critical, Error


def parse_syslog_pri(message):
    """
    Parse syslog priority from message.

    Syslog messages start with <PRI> where PRI is a number.
    Facility = PRI / 8
    Severity = PRI % 8

    Returns: (facility, severity, message_without_pri) or (None, None, message)
    """
    # Match <NNN> at the start of the message
    pri_match = re.match(r'^<(\d+)>(.*)$', message)

    if pri_match:
        pri = int(pri_match.group(1))
        remaining_message = pri_match.group(2)

        facility = pri // 8
        severity = pri % 8

        return facility, severity, remaining_message

    return None, None, message


def parse_syslog_message(message_without_pri):
    """
    Parse syslog message to extract actual message text.

    Handles both RFC 5424 and RFC 3164 formats.

    RFC 5424: VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    RFC 3164: Mmm dd hh:mm:ss HOSTNAME MESSAGE

    Returns: (hostname, app_name, actual_message_text)
    """
    # Check if it's RFC 5424 format (starts with version number, typically "1 ")
    if message_without_pri.startswith("1 "):
        # RFC 5424 format
        # First get the basic fields (up to MSGID)
        parts = message_without_pri.split(None, 6)  # Split first 6 fields

        if len(parts) >= 7:
            # parts[0] = VERSION (1)
            # parts[1] = TIMESTAMP
            # parts[2] = HOSTNAME
            # parts[3] = APP-NAME
            # parts[4] = PROCID
            # parts[5] = MSGID
            # parts[6] = STRUCTURED-DATA + MSG (remainder)

            hostname = parts[2] if parts[2] != "-" else "unknown"
            app_name = parts[3] if parts[3] != "-" else "unknown"

            # Now handle STRUCTURED-DATA and MSG
            remainder = parts[6]

            # If STRUCTURED-DATA is nil (-)
            if remainder.startswith("- "):
                actual_message = remainder[2:]  # Skip "- " prefix
            # If STRUCTURED-DATA starts with [
            elif remainder.startswith("["):
                # Find the end of structured data (matching closing bracket)
                bracket_count = 0
                end_index = 0
                for i, char in enumerate(remainder):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_index = i + 1
                            break

                # Extract message after structured data
                if end_index > 0 and end_index < len(remainder):
                    actual_message = remainder[end_index:].lstrip()
                else:
                    actual_message = ""
            else:
                # No structured data, remainder is the message
                actual_message = remainder

            return hostname, app_name, actual_message

        # Malformed RFC 5424, return what we have
        return "unknown", "unknown", message_without_pri

    # Try RFC 3164 format (legacy)
    # Pattern: Mmm dd hh:mm:ss HOSTNAME MESSAGE
    rfc3164_match = re.match(r'^([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)$', message_without_pri)

    if rfc3164_match:
        timestamp = rfc3164_match.group(1)
        hostname = rfc3164_match.group(2)
        message_text = rfc3164_match.group(3)

        # Try to extract app name from message (format: "appname[pid]: message" or "appname: message")
        app_match = re.match(r'^(\S+?)(?:\[\d+\])?:\s*(.*)$', message_text)
        if app_match:
            app_name = app_match.group(1)
            actual_message = app_match.group(2)
        else:
            app_name = "unknown"
            actual_message = message_text

        return hostname, app_name, actual_message

    # Unknown format, return the whole thing as the message
    return "unknown", "unknown", message_without_pri


def start_syslog_listener(state_manager, host="0.0.0.0", port=514):
    """
    Start UDP syslog listener.

    Args:
        state_manager: StateManager instance for thread-safe state access
        host: IP address to bind to (default: 0.0.0.0 for all interfaces)
        port: UDP port to listen on (default: 514)
    """
    print(f"[Syslog Listener] Starting on {host}:{port}")

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind((host, port))
        print(f"[Syslog Listener] Bound to {host}:{port}")

        # Initialize stats in state
        with state_manager.state_lock() as state:
            if 'stats' not in state:
                state['stats'] = {}
            state['stats']['syslog_count'] = 0

            if 'recent_alerts' not in state:
                state['recent_alerts'] = []

        # Main receive loop
        while True:
            try:
                # Receive data (max 1024 bytes)
                data, addr = sock.recvfrom(1024)

                # Decode to text, handling UTF-8 errors gracefully
                try:
                    message = data.decode('utf-8')
                except UnicodeDecodeError:
                    # Fall back to latin-1 or ignore errors
                    message = data.decode('utf-8', errors='ignore')

                # Parse syslog priority
                facility, severity, message_without_pri = parse_syslog_pri(message)

                # Parse the syslog message format to extract actual message text
                hostname, app_name, actual_message = parse_syslog_message(message_without_pri)

                # Prepare log entry
                timestamp = datetime.now().isoformat()
                severity_name = SEVERITY_NAMES.get(severity, "Unknown") if severity is not None else "Unknown"

                log_entry = {
                    'timestamp': timestamp,
                    'source': f"{addr[0]}:{addr[1]}",
                    'hostname': hostname,
                    'app_name': app_name,
                    'facility': facility,
                    'severity': severity,
                    'severity_name': severity_name,
                    'message': actual_message
                }

                # Update state with thread-safe locking
                with state_manager.state_lock() as state:
                    # Increment counter
                    state['stats']['syslog_count'] += 1

                    # Add to recent alerts if high severity
                    if severity is not None and severity in HIGH_SEVERITY:
                        state['recent_alerts'].append(log_entry)

                        # Keep only last 100 alerts
                        if len(state['recent_alerts']) > 100:
                            state['recent_alerts'] = state['recent_alerts'][-100:]

                        print(f"{timestamp} [{severity_name}] {hostname} - {actual_message[:80]}")
                    else:
                        print(f"{timestamp} [{severity_name}] {hostname} - {actual_message[:80]}")

            except Exception as e:
                # Handle exceptions to prevent crash on bad packets
                print(f"[Syslog Listener] Error processing packet: {e}")
                continue

    except Exception as e:
        print(f"[Syslog Listener] Fatal error: {e}")
    finally:
        sock.close()
        print("[Syslog Listener] Stopped")
