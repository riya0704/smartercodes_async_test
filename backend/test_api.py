import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Check if the API is up and running"""
    print("Checking health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        print(f"✓ Server is up: {resp.json()}")
        return True
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        return False

def test_search():
    """Try a real search to make sure everything works"""
    print("\nTesting search...")
    
    test_data = {
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "query": "programming language features"
    }
    
    try:
        print(f"URL: {test_data['url']}")
        print(f"Query: '{test_data['query']}'")
        
        resp = requests.post(
            f"{BASE_URL}/api/search",
            json=test_data,
            timeout=60
        )
        resp.raise_for_status()
        
        data = resp.json()
        results = data.get("results", [])
        
        print(f"\n✓ Got {len(results)} results!")
        
        if results:
            print("\nTop 3 matches:")
            for i, result in enumerate(results[:3], 1):
                preview = result['content'][:80] + "..."
                print(f"\n{i}. Match: {result['score']:.2%}")
                print(f"   {preview}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("✗ Timed out - first request can be slow while models load")
        print("  Wait a minute and try again")
        return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    print("=" * 50)
    print("API Test")
    print("=" * 50)
    print("\nMake sure the backend is running first!")
    print("(run_server.bat or uvicorn command)\n")
    
    time.sleep(2)
    
    # Run the tests
    health_ok = test_health()
    
    if health_ok:
        search_ok = test_search()
        
        print("\n" + "=" * 50)
        if search_ok:
            print("✓ Everything works!")
        else:
            print("✗ Search test failed")
        print("=" * 50)
    else:
        print("\n✗ Can't reach the backend - is it running?")

if __name__ == "__main__":
    main()
