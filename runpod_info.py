#!/usr/bin/env python3
"""Quick reference script for RunPod connection information."""

import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

from config import ConfigLoader

def main():
    config = ConfigLoader.load()
    rp = config.runpod

    print("\n" + "="*60)
    print("RUNPOD CONNECTION INFORMATION")
    print("="*60)

    print(f"\n🚀 Pod: {rp.pod_name} (ID: {rp.pod_id})")

    print("\n📡 CONNECTION METHODS:")
    print("-" * 40)

    print("\n1. SSH via RunPod proxy:")
    print(f"   ssh {rp.ssh_user}@{rp.ssh_host} -i ~/.ssh/id_ed25519")

    print("\n2. Direct SSH over TCP (supports SCP/SFTP):")
    print(f"   ssh {rp.ssh_tcp_user}@{rp.ssh_tcp_host} -p {rp.ssh_tcp_port} -i ~/.ssh/id_ed25519")

    print("\n3. HTTP Service (Port {})".format(rp.service_port))
    print(f"   {rp.http_proxy_url}")
    print("   Status: Check RunPod dashboard for readiness")

    print("\n4. Jupyter Lab (Port {})".format(rp.jupyter_port))
    print(f"   Access via RunPod dashboard when ready")

    print("\n📦 FILE TRANSFER:")
    print("-" * 40)
    print(f"SCP:  scp -P {rp.ssh_tcp_port} -i ~/.ssh/id_ed25519 <file> {rp.ssh_tcp_user}@{rp.ssh_tcp_host}:~/")
    print(f"SFTP: sftp -P {rp.ssh_tcp_port} -i ~/.ssh/id_ed25519 {rp.ssh_tcp_user}@{rp.ssh_tcp_host}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()