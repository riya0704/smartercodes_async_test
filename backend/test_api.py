"""
Simple test script to verify the backend API is working correctly.
Run this after starting the backend and Weaviate services.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print(f"✓ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_search():
    """Test the search endpoint with a sample URL"""
    print("\nTesting /api/search endpoint...")
    
    payload = {
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "query": "programming language features"
    }
    
    try:
        print(f"Sending request with URL: {payload['url']}")
        print(f"Query: {payload['query']}")
        
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        print(f"\n✓ Search successful! Found {len(results)} results")
        
        if results:
            print("\nTop 3 results:")
            for i, result in enumerate(results[:3], 1):
                content_preview = result['content'][:100] + "..."
                print(f"\n{i}. Score: {result['score']:.4f}")
                print(f"   Content: {content_preview}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("✗ Request timed out (this is normal for first request as models load)")
        print("  Try running the test again in a few minutes")
        return False
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Backend API Test Suite")
    print("=" * 60)
    print("\nMake sure the backend and Weaviate are running:")
    print("  docker-compose up")
    print("\nWaiting 5 seconds for services to be ready...")
    time.sleep(5)
    
    # Run tests
    health_ok = test_health()
    
    if health_ok:
        search_ok = test_search()
        
        print("\n" + "=" * 60)
        if health_ok and search_ok:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed. Check the output above.")
        print("=" * 60)
    else:
        print("\n✗ Backend is not responding. Check if services are running.")

if __name__ == "__main__":
    main()
