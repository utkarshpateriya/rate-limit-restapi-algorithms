"""
Client for testing and demonstrating rate limiting algorithms.
"""

import requests
import time
from typing import List, Dict
import json


class RateLimitTester:
    """Test client for rate limiting demonstration."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_endpoint(
        self,
        endpoint: str,
        num_requests: int = 15,
        delay_between_requests: float = 0.1
    ) -> List[Dict]:
        """
        Test an endpoint by making multiple rapid requests.

        Args:
            endpoint: The endpoint to test (e.g., "/fixed-window")
            num_requests: Number of requests to make
            delay_between_requests: Delay in seconds between requests

        Returns:
            List of response data for each request
        """
        url = f"{self.base_url}{endpoint}"
        results = []

        print(f"\n{'='*70}")
        print(f"Testing: {endpoint}")
        print(f"Making {num_requests} requests with {delay_between_requests}s delay")
        print(f"{'='*70}")

        for i in range(num_requests):
            try:
                start_time = time.time()
                response = self.session.get(url)
                elapsed = time.time() - start_time

                status_code = response.status_code
                success = status_code == 200

                result = {
                    "request_num": i + 1,
                    "status_code": status_code,
                    "success": success,
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "response": response.json() if response.text else {}
                }

                results.append(result)

                # Print result
                status_symbol = "✓" if success else "✗"
                print(f"  [{status_symbol}] Request {i+1:2d}: HTTP {status_code} ({elapsed*1000:.1f}ms)")

                if not success:
                    if "detail" in response.json():
                        print(f"      Error: {response.json()['detail']}")

                if i < num_requests - 1:
                    time.sleep(delay_between_requests)

            except requests.exceptions.RequestException as e:
                print(f"  [✗] Request {i+1:2d}: Error - {e}")
                results.append({
                    "request_num": i + 1,
                    "error": str(e)
                })

        # Print summary
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        print(f"\nSummary: {successful} successful, {failed} rate limited")

        return results

    def test_all_algorithms(self, num_requests: int = 15):
        """Test all rate limiting algorithms."""
        endpoints = [
            "/fixed-window",
            "/sliding-window-log",
            "/sliding-window-counter",
            "/token-bucket",
            "/leaky-bucket"
        ]

        all_results = {}

        for endpoint in endpoints:
            results = self.test_endpoint(endpoint, num_requests=num_requests)
            all_results[endpoint] = results

        return all_results

    def get_algorithm_info(self, algorithm: str = None) -> Dict:
        """Get information about algorithms."""
        url = f"{self.base_url}/info"
        params = {"algorithm": algorithm} if algorithm else {}

        try:
            response = self.session.get(url, params=params)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting info: {e}")
            return {}

    def health_check(self) -> bool:
        """Check if the API is running."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


def main():
    """Main function to demonstrate rate limiting."""
    print("Rate Limiting Algorithm Tester")
    print("="*70)

    # Create client
    client = RateLimitTester()

    # Check if server is running
    if not client.health_check():
        print("ERROR: Could not connect to the API server.")
        print("Make sure to run: python main.py")
        return

    print("✓ Connected to API server\n")

    # Test options
    print("Test Options:")
    print("  1. Test specific algorithm")
    print("  2. Test all algorithms")
    print("  3. Get algorithm information")
    print("  4. Exit")

    while True:
        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            print("\nAvailable endpoints:")
            endpoints = [
                "/fixed-window",
                "/sliding-window-log",
                "/sliding-window-counter",
                "/token-bucket",
                "/leaky-bucket"
            ]
            for i, ep in enumerate(endpoints, 1):
                print(f"  {i}. {ep}")

            endpoint_choice = input("Select endpoint (1-5): ").strip()
            if endpoint_choice.isdigit() and 1 <= int(endpoint_choice) <= 5:
                endpoint = endpoints[int(endpoint_choice) - 1]
                num_requests = input("Number of requests to make (default 15): ").strip()
                num_requests = int(num_requests) if num_requests.isdigit() else 15

                client.test_endpoint(endpoint, num_requests=num_requests)

        elif choice == "2":
            num_requests = input("Number of requests per algorithm (default 15): ").strip()
            num_requests = int(num_requests) if num_requests.isdigit() else 15
            client.test_all_algorithms(num_requests=num_requests)

        elif choice == "3":
            info = client.get_algorithm_info()
            print("\n" + "="*70)
            print("Rate Limiting Algorithms Information")
            print("="*70)
            for algo, details in info.items():
                print(f"\n{algo}:")
                print(f"  Pros: {', '.join(details['pros'])}")
                print(f"  Cons: {', '.join(details['cons'])}")
                print(f"  Use Case: {details['use_case']}")

        elif choice == "4":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
