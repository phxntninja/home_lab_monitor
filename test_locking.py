#!/usr/bin/env python3
"""Test script to demonstrate thread-safe state management with context manager locking."""

import threading
import time
from contextlib import contextmanager


class StateManager:
    """Manages shared state with thread-safe locking."""

    def __init__(self):
        self._state = {}
        self._lock = threading.Lock()

    @contextmanager
    def state_lock(self):
        """Context manager for thread-safe state access."""
        self._lock.acquire()
        try:
            yield self._state
        finally:
            self._lock.release()


def worker_thread(name, state_manager, iterations=5):
    """Worker thread that updates shared state."""
    for i in range(iterations):
        with state_manager.state_lock() as state:
            # Read current counter
            current = state.get('counter', 0)

            # Simulate some work
            time.sleep(0.01)

            # Update counter
            state['counter'] = current + 1
            state[f'last_update_{name}'] = i

            print(f"[{name}] Iteration {i}: counter={state['counter']}")


def main():
    print("Testing thread-safe state management with context manager locking\n")

    # Create shared state manager
    state_manager = StateManager()

    # Initialize state
    with state_manager.state_lock() as state:
        state['counter'] = 0
        print(f"Initial state: {state}\n")

    # Create and start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(
            target=worker_thread,
            args=(f"Thread-{i+1}", state_manager),
            daemon=True
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Display final state
    with state_manager.state_lock() as state:
        print(f"\nFinal state: {state}")
        expected_counter = 15  # 3 threads * 5 iterations
        if state['counter'] == expected_counter:
            print(f"\n✓ SUCCESS: Counter is {expected_counter} as expected!")
            print("  Locking mechanism prevented race conditions.")
        else:
            print(f"\n✗ FAILURE: Counter is {state['counter']}, expected {expected_counter}")
            print("  Race condition detected!")


if __name__ == "__main__":
    main()
