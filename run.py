import subprocess
import sys
import os
import signal

def main():
    print("Starting ULPF Backend and Frontend concurrently...")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start Backend
    print("[*] Starting backend (uvicorn)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--reload", "--port", "8000"],
        cwd=root_dir
    )
    
    # Start Frontend
    print("[*] Starting frontend (vite)...")
    frontend_cwd = os.path.join(root_dir, "ulpf-ui")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_cwd
    )
    
    def signal_handler(sig, frame):
        print("\n[*] Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("\n[+] Both servers are running. Press Ctrl+C to stop.\n")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
