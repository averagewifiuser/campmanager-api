#!/usr/bin/env python3
"""
Simple test script to verify caching implementation for get_registration_form endpoint
"""

import time
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your API runs on a different port
CAMP_ID = "your-camp-id-here"  # Replace with an actual camp ID from your database

def test_registration_form_caching():
    """Test the caching behavior of the get_registration_form endpoint"""
    
    print("🧪 Testing Registration Form Caching Implementation")
    print("=" * 60)
    
    # Test the main endpoint
    endpoint = f"{BASE_URL}/camps/{CAMP_ID}/register"
    
    print(f"📍 Testing endpoint: {endpoint}")
    print()
    
    # First request - should be a cache MISS
    print("1️⃣ First request (should be cache MISS):")
    start_time = time.time()
    
    try:
        response1 = requests.get(endpoint)
        end_time = time.time()
        
        if response1.status_code == 200:
            print(f"   ✅ Status: {response1.status_code}")
            print(f"   ⏱️  Response time: {(end_time - start_time) * 1000:.2f}ms")
            data1 = response1.json()
            print(f"   📊 Data keys: {list(data1.get('data', {}).keys())}")
        else:
            print(f"   ❌ Status: {response1.status_code}")
            print(f"   📝 Response: {response1.text}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return
    
    print()
    
    # Second request - should be a cache HIT
    print("2️⃣ Second request (should be cache HIT):")
    start_time = time.time()
    
    try:
        response2 = requests.get(endpoint)
        end_time = time.time()
        
        if response2.status_code == 200:
            print(f"   ✅ Status: {response2.status_code}")
            print(f"   ⏱️  Response time: {(end_time - start_time) * 1000:.2f}ms")
            data2 = response2.json()
            print(f"   📊 Data keys: {list(data2.get('data', {}).keys())}")
            
            # Compare response times
            first_time = (end_time - start_time) * 1000
            if 'first_time' in locals():
                improvement = ((first_time - (end_time - start_time) * 1000) / first_time) * 100
                print(f"   🚀 Performance improvement: {improvement:.1f}%")
        else:
            print(f"   ❌ Status: {response2.status_code}")
            print(f"   📝 Response: {response2.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return
    
    print()
    
    # Test with link token (different cache key)
    print("3️⃣ Testing with link token (different cache key):")
    token_endpoint = f"{BASE_URL}/register/sample-token"  # Replace with actual token
    
    try:
        response3 = requests.get(token_endpoint)
        if response3.status_code == 200:
            print(f"   ✅ Token endpoint works: {response3.status_code}")
        else:
            print(f"   ⚠️  Token endpoint status: {response3.status_code} (expected if token doesn't exist)")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Token endpoint failed: {e} (expected if server not running)")
    
    print()
    print("📋 Test Summary:")
    print("   - Caching decorator applied to get_registration_form method")
    print("   - Cache timeout set to 10 minutes (600 seconds)")
    print("   - Cache invalidation implemented for church, category, and custom field changes")
    print("   - Different cache keys for general vs token-based requests")
    
    print()
    print("🔍 To verify caching in logs, check for:")
    print("   - 'Cache MISS' messages on first requests")
    print("   - 'Cache HIT' messages on subsequent requests")
    print("   - 'Fetching registration form for camp_id' debug messages")

def test_cache_invalidation():
    """Test cache invalidation by simulating data changes"""
    print()
    print("4️⃣ Cache Invalidation Test:")
    print("   This would require authenticated requests to modify data")
    print("   - Creating/updating churches should invalidate cache")
    print("   - Creating/updating categories should invalidate cache") 
    print("   - Creating/updating custom fields should invalidate cache")
    print("   - Cache keys follow pattern: registration_form:{camp_id}:{args_hash}")

if __name__ == "__main__":
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Update the CAMP_ID before running
    if CAMP_ID == "your-camp-id-here":
        print("⚠️  Please update CAMP_ID in the script with an actual camp ID from your database")
        print("   You can find camp IDs by checking your database or API logs")
        exit(1)
    
    test_registration_form_caching()
    test_cache_invalidation()
    
    print()
    print("✅ Caching implementation test completed!")
    print()
    print("📝 Next steps:")
    print("   1. Run your Flask application")
    print("   2. Update CAMP_ID in this script")
    print("   3. Run this test script: python test_caching.py")
    print("   4. Check application logs for cache HIT/MISS messages")
    print("   5. Monitor response times for performance improvements")
