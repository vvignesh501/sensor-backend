"""
Automated Security Testing Script
Tests JWT authentication, authorization, and security features
"""
import requests
import json
from typing import Dict

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def test_health_check():
    """Test health check endpoint"""
    print_test("Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print_success("Health check passed")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print_error(f"Health check failed: {response.status_code}")
        return False


def test_login(username: str, password: str) -> Dict:
    """Test login and return tokens"""
    print_test(f"Login as {username}")
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        tokens = response.json()
        print_success(f"Login successful for {username}")
        print_info(f"Access Token: {tokens['access_token'][:50]}...")
        print_info(f"Refresh Token: {tokens['refresh_token'][:50]}...")
        return tokens
    else:
        print_error(f"Login failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return {}


def test_invalid_login():
    """Test login with invalid credentials"""
    print_test("Invalid Login Attempt")
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": "invalid", "password": "wrong"}
    )
    
    if response.status_code == 401:
        print_success("Invalid login correctly rejected (401)")
        return True
    else:
        print_error(f"Expected 401, got {response.status_code}")
        return False


def test_get_current_user(access_token: str):
    """Test getting current user info"""
    print_test("Get Current User")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print_success("User info retrieved")
        print_info(f"User: {json.dumps(user, indent=2)}")
        return user
    else:
        print_error(f"Failed to get user: {response.status_code}")
        return None


def test_access_protected_endpoint(access_token: str):
    """Test accessing protected sensor endpoint"""
    print_test("Access Protected Endpoint (GET /sensors)")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/v1/sensors/", headers=headers)
    
    if response.status_code == 200:
        sensors = response.json()
        print_success(f"Retrieved {len(sensors)} sensors")
        print_info(f"Sensors: {json.dumps(sensors, indent=2, default=str)}")
        return True
    else:
        print_error(f"Failed to access endpoint: {response.status_code}")
        return False


def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    print_test("Unauthorized Access (No Token)")
    
    response = requests.get(f"{BASE_URL}/api/v1/sensors/")
    
    if response.status_code == 401:
        print_success("Unauthorized access correctly rejected (401)")
        return True
    else:
        print_error(f"Expected 401, got {response.status_code}")
        return False


def test_create_sensor(access_token: str):
    """Test creating sensor data (requires 'write' scope)"""
    print_test("Create Sensor Data (POST /sensors)")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    sensor_data = {
        "sensor_id": "TEST_SENSOR_001",
        "temperature": 25.5,
        "humidity": 55.0,
        "timestamp": "2024-01-01T12:00:00",
        "location": "Test_Building"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/sensors/",
        headers=headers,
        json=sensor_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print_success("Sensor data created")
        print_info(f"Response: {json.dumps(result, indent=2, default=str)}")
        return True
    else:
        print_error(f"Failed to create sensor: {response.status_code}")
        print_error(f"Response: {response.text}")
        return False


def test_delete_sensor_without_admin(access_token: str):
    """Test deleting sensor without admin scope"""
    print_test("Delete Sensor Without Admin Scope")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.delete(
        f"{BASE_URL}/api/v1/sensors/SENSOR_001",
        headers=headers
    )
    
    if response.status_code == 403:
        print_success("Delete correctly rejected without admin scope (403)")
        return True
    else:
        print_error(f"Expected 403, got {response.status_code}")
        return False


def test_refresh_token(refresh_token: str):
    """Test refreshing access token"""
    print_test("Refresh Access Token")
    
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    if response.status_code == 200:
        tokens = response.json()
        print_success("Token refreshed successfully")
        print_info(f"New Access Token: {tokens['access_token'][:50]}...")
        return tokens
    else:
        print_error(f"Failed to refresh token: {response.status_code}")
        return {}


def test_security_headers():
    """Test security headers in response"""
    print_test("Security Headers")
    
    response = requests.get(f"{BASE_URL}/")
    headers = response.headers
    
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
    
    all_present = True
    for header, expected_value in security_headers.items():
        if header in headers:
            print_success(f"{header}: {headers[header]}")
        else:
            print_error(f"{header}: MISSING")
            all_present = False
    
    return all_present


def run_all_tests():
    """Run complete security test suite"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🔐 SECURITY TEST SUITE{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Security headers
    results.append(("Security Headers", test_security_headers()))
    
    # Test 3: Invalid login
    results.append(("Invalid Login", test_invalid_login()))
    
    # Test 4: Unauthorized access
    results.append(("Unauthorized Access", test_unauthorized_access()))
    
    # Test 5: Valid login (regular user)
    user_tokens = test_login("sensor_user", "sensor123")
    results.append(("User Login", bool(user_tokens)))
    
    if user_tokens:
        # Test 6: Get current user
        user = test_get_current_user(user_tokens["access_token"])
        results.append(("Get Current User", user is not None))
        
        # Test 7: Access protected endpoint
        results.append(("Access Protected Endpoint", 
                       test_access_protected_endpoint(user_tokens["access_token"])))
        
        # Test 8: Create sensor data
        results.append(("Create Sensor Data", 
                       test_create_sensor(user_tokens["access_token"])))
        
        # Test 9: Delete without admin (should fail)
        results.append(("Delete Without Admin", 
                       test_delete_sensor_without_admin(user_tokens["access_token"])))
        
        # Test 10: Refresh token
        new_tokens = test_refresh_token(user_tokens["refresh_token"])
        results.append(("Refresh Token", bool(new_tokens)))
    
    # Test 11: Admin login
    admin_tokens = test_login("admin", "admin123")
    results.append(("Admin Login", bool(admin_tokens)))
    
    # Print summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All tests passed!{Colors.END}")
    else:
        print(f"{Colors.RED}✗ Some tests failed{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}Make sure the secure API is running:{Colors.END}")
    print(f"{Colors.YELLOW}  python app/secure_app.py{Colors.END}\n")
    
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the API is running!{Colors.END}\n")
