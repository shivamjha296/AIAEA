import httpx
import time
import sys
import os

API_BASE = "http://localhost:8000"

# List of endpoints to verify
ENDPOINTS = [
    ("GET", "/api/health", None),
    ("GET", "/api/dashboard/metrics", None),
    ("GET", "/api/dashboard/activity", {"days": 30}),
    ("GET", "/api/dashboard/regulators", None),
    ("GET", "/api/regulations", {"page": 1, "page_size": 20}),
    ("GET", "/api/regulations/regulators", None),
    ("GET", "/api/risk", {"page": 1, "page_size": 50}),
    ("GET", "/api/risk/distribution", None),
    ("GET", "/api/security/events", {"limit": 50}),
    ("GET", "/api/security/metrics", None),
    ("GET", "/api/reviews/pending", None),
    ("GET", "/api/reviews/history", None),
    ("GET", "/api/scans", None),
    ("GET", "/api/audit", {"limit": 100}),
]

def verify_endpoints():
    print(f"=== Starting API Verification against {API_BASE} ===")
    
    # 1. Health check first
    try:
        r = httpx.get(f"{API_BASE}/api/health", timeout=5)
        print(f"GET /api/health -> {r.status_code}")
        if r.status_code != 200:
            print("API is not running. Start the API first.")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to connect to API: {e}")
        sys.exit(1)

    # 2. Test standard GET endpoints
    for method, path, params in ENDPOINTS:
        try:
            url = f"{API_BASE}{path}"
            r = httpx.request(method, url, params=params)
            print(f"{method} {path} -> {r.status_code}")
            if r.status_code != 200:
                print(f"  Error: {r.text}")
        except Exception as e:
            print(f"{method} {path} -> Failed: {e}")

    # 3. Test parameter-dependent endpoints
    print("\n--- Testing dynamic endpoints ---")
    
    # Get a regulation ID
    regs_r = httpx.get(f"{API_BASE}/api/regulations")
    regs_data = regs_r.json()
    reg_items = regs_data.get("items", [])
    
    if reg_items:
        reg_id = reg_items[0]["id"]
        
        # GET /api/regulations/{id}
        r = httpx.get(f"{API_BASE}/api/regulations/{reg_id}")
        print(f"GET /api/regulations/{{id}} -> {r.status_code}")
        
        # GET /api/regulations/{id}/export
        r = httpx.get(f"{API_BASE}/api/regulations/{reg_id}/export")
        print(f"GET /api/regulations/{{id}}/export -> {r.status_code}")
        
    else:
        print("No regulations found to test detail endpoints.")

    # Test POST /api/scans
    print("\n--- Testing POST /api/scans ---")
    try:
        r = httpx.post(f"{API_BASE}/api/scans", json={"max_queries": 1, "max_sources": 1})
        print(f"POST /api/scans -> {r.status_code}")
        if r.status_code == 200:
            scan_data = r.json()
            scan_id = scan_data.get("scan_id")
            print(f"  Created scan: {scan_id}")
    except Exception as e:
        print(f"POST /api/scans -> Failed: {e}")

    # Get a review ID
    reviews_r = httpx.get(f"{API_BASE}/api/reviews/pending")
    reviews_data = reviews_r.json()
    
    if reviews_data:
        review_id = reviews_data[0]["id"]
        
        # We won't test approve/reject blindly to avoid corrupting data, but we will test it with an invalid ID to check 404
        r = httpx.post(f"{API_BASE}/api/reviews/999999/approve", json={"reviewer": "test", "reason": "test"})
        print(f"POST /api/reviews/{{id}}/approve (invalid ID) -> {r.status_code} (Expected 404)")
        
        r = httpx.post(f"{API_BASE}/api/reviews/999999/reject", json={"reviewer": "test", "reason": "test"})
        print(f"POST /api/reviews/{{id}}/reject (invalid ID) -> {r.status_code} (Expected 404)")
    else:
        print("No pending reviews found. Will test with invalid ID.")
        r = httpx.post(f"{API_BASE}/api/reviews/999999/approve", json={"reviewer": "test", "reason": "test"})
        print(f"POST /api/reviews/{{id}}/approve (invalid ID) -> {r.status_code} (Expected 404)")

    # Get a scan ID
    scans_r = httpx.get(f"{API_BASE}/api/scans")
    scans_data = scans_r.json()
    
    if scans_data:
        scan = scans_data[0]
        scan_id = scan.get("id") or scan.get("scan_id")
        
        # GET /api/scans/{scan_id}
        r = httpx.get(f"{API_BASE}/api/scans/{scan_id}")
        print(f"GET /api/scans/{{id}} -> {r.status_code}")
        
        # GET /api/scans/{scan_id}/events (SSE)
        # We just stream 1 event or connect and disconnect
        print(f"GET /api/scans/{{id}}/events (SSE) -> Testing connection...")
        try:
            with httpx.stream("GET", f"{API_BASE}/api/scans/{scan_id}/events") as r:
                print(f"SSE Connection -> {r.status_code}")
                # read first chunk
                for chunk in r.iter_text():
                    if chunk:
                        print(f"SSE First chunk received.")
                        break
        except Exception as e:
            print(f"SSE Stream failed: {e}")
            
    else:
        print("No scans found to test detail endpoints.")
        
    print("\n=== API Verification Complete ===")

if __name__ == "__main__":
    verify_endpoints()
