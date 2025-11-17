"""Quick test script to verify server functionality."""
import requests
import sys


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        print(f"✓ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_synthesize():
    """Test synthesis endpoint."""
    print("\nTesting synthesis endpoint...")
    try:
        payload = {
            "text": "Hello, this is a test of the Maya1 text to speech system.",
            "voice_description": "neutral, conversational"
        }

        print("Sending request...")
        response = requests.post(
            "http://localhost:8000/synthesize",
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        # Save output
        output_file = "test_output.mp3"
        with open(output_file, "wb") as f:
            f.write(response.content)

        print(f"✓ Synthesis successful!")
        print(f"  Output saved to: {output_file}")
        print(f"  File size: {len(response.content)} bytes")
        return True

    except Exception as e:
        print(f"✗ Synthesis failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Maya1 Server Test Suite")
    print("=" * 50)

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health()))

    # Test 2: Synthesis
    results.append(("Synthesis", test_synthesize()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")

    # Exit code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
