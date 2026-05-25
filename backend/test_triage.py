import requests
import sys

url = "http://127.0.0.1:8000/api/triage"
payload = {
    "volunteers_scheduled": 4,
    "volunteers_present": 1,
    "key_roles_missing": ["Till Operator", "Stock Sorter"],
    "donation_bags_clothing": 30,
    "donation_boxes_misc": 10,
    "donation_high_value_items": ["designer handbag", "box of retro vinyl records"],
    "daily_revenue_target": 500.0,
    "current_campaign_focus": "Stand Up To Cancer"
}

def run_test():
    print(f"Testing connectivity to {url}...")
    try:
        # Check health endpoint first
        health_resp = requests.get("http://127.0.0.1:8000/api/health")
        print("Health check response:", health_resp.json())
        
        # Test triage endpoint
        response = requests.post(url, json=payload)
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print("\n--- AI Smart Triage Action Plan ---")
            print(response.json()["triage_plan"])
            print("----------------------------------\n")
            print("Test successful!")
        else:
            print("Test failed with status code:", response.status_code)
            print("Error detail:", response.json())
            sys.exit(1)
    except Exception as e:
        print("Failed to run test. Is the backend server running?", e)
        sys.exit(1)

if __name__ == "__main__":
    run_test()
