import sys
import os
import time

# Ensure UTF-8 encoding for Linux console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure workspace root is in sys.path
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from checker import run_checker_once

def main():
    print("🚀 Starting Cloud Check Block (10 iterations spaced 30 seconds apart)...")
    for i in range(10):
        print(f"\n--- ⏱️ Iteration {i+1}/10 ---")
        try:
            found = run_checker_once()
            if found:
                print("🎉 Ticket release detected and notified!")
        except Exception as e:
            print(f"⚠️ Iteration {i+1} error: {e}")
            
        if i < 9:
            time.sleep(30)

if __name__ == "__main__":
    main()
