#!/usr/bin/env python3
"""Test script for syslog listener."""

import sys
import threading
sys.path.insert(0, '.')

from test_locking import StateManager
from app.monitors.syslog_listener import start_syslog_listener


def main():
    print("Starting Syslog Listener Test\n")
    print("Press Ctrl+C to stop\n")

    # Create state manager
    state_manager = StateManager()

    # Start syslog listener in a daemon thread
    # Using port 5514 to avoid needing root privileges
    listener_thread = threading.Thread(
        target=start_syslog_listener,
        args=(state_manager, "0.0.0.0", 5514),
        daemon=True
    )
    listener_thread.start()

    try:
        # Keep main thread alive and show stats periodically
        import time
        while True:
            time.sleep(5)
            with state_manager.state_lock() as state:
                stats = state.get('stats', {})
                alerts = state.get('recent_alerts', [])
                print(f"\n--- Stats: {stats.get('syslog_count', 0)} messages, {len(alerts)} alerts ---")
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        with state_manager.state_lock() as state:
            print(f"\nFinal stats: {state.get('stats', {})}")
            print(f"Total alerts: {len(state.get('recent_alerts', []))}")


if __name__ == "__main__":
    main()
