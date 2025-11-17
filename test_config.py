#!/usr/bin/env python3
"""Test script to verify RunPod configuration is loaded correctly."""

import json
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

try:
    from config_schema import AppConfig
    from config import ConfigLoader

    print("Testing configuration loading...")

    # Load configuration
    config = ConfigLoader.load()

    print("\n✓ Configuration loaded successfully!")

    # Display RunPod configuration
    print("\n=== RunPod Configuration ===")
    print(f"Pod Name: {config.runpod.pod_name}")
    print(f"Pod ID: {config.runpod.pod_id}")
    print(f"SSH Connection: {config.runpod.ssh_user}@{config.runpod.ssh_host}")
    print(f"SSH over TCP: {config.runpod.ssh_tcp_user}@{config.runpod.ssh_tcp_host}:{config.runpod.ssh_tcp_port}")
    print(f"Direct TCP: {config.runpod.direct_tcp_address}:{config.runpod.direct_tcp_port}")
    print(f"HTTP Proxy URL: {config.runpod.http_proxy_url}")
    print(f"Jupyter Port: {config.runpod.jupyter_port}")
    print(f"Service Port: {config.runpod.service_port}")

    print("\n=== Server Configuration ===")
    print(f"Host: {config.server.host}")
    print(f"Port: {config.server.port}")

    print("\n=== Connection Commands ===")
    print(f"SSH: ssh {config.runpod.ssh_user}@{config.runpod.ssh_host} -i ~/.ssh/id_ed25519")
    print(f"SSH over TCP: ssh {config.runpod.ssh_tcp_user}@{config.runpod.ssh_tcp_host} -p {config.runpod.ssh_tcp_port} -i ~/.ssh/id_ed25519")
    print(f"HTTP Service: {config.runpod.http_proxy_url}")

    print("\n✓ All configuration values are accessible!")

except Exception as e:
    print(f"\n✗ Error loading configuration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)