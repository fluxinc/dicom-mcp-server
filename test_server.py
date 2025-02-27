#!/usr/bin/env python3
"""
Test script for DICOM MCP Server
This script attempts to import the required dependencies and run a basic test
"""
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []

    try:
        import mcp.server.fastmcp
        print("✓ mcp.server.fastmcp is installed")
    except ImportError as e:
        print(f"✗ Failed to import mcp.server.fastmcp: {e}")
        missing_deps.append("mcp-server")

    try:
        import pynetdicom
        print(f"✓ pynetdicom {pynetdicom.__version__} is installed")
    except ImportError as e:
        print(f"✗ Failed to import pynetdicom: {e}")
        missing_deps.append("pynetdicom")

    return missing_deps

def main():
    """Main test function"""
    print("Testing DICOM MCP Server dependencies...")

    missing = check_dependencies()

    if missing:
        print("\nMissing dependencies detected. Please install them with:")
        print(f"pip install {' '.join(missing)}")
        return 1

    print("\nAll dependencies are installed correctly.")
    print("To run the server, use: python server.py")

    # Try to import the server module
    try:
        import server
        print("✓ Server module can be imported")
    except Exception as e:
        print(f"✗ Failed to import server module: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
