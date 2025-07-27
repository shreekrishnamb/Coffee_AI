#!/usr/bin/env python3
"""
Integration test script for Coffee AI Backend-Frontend
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_backend_health():
    """Test if backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test API root
    try:
        response = requests.get(f"{base_url}/api/v1/")
        if response.status_code == 200:
            print("✅ API root endpoint working")
        else:
            print(f"❌ API root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API root endpoint error: {e}")
    
    # Test products endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/products/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Products endpoint working - {len(data.get('products', []))} products loaded")
        else:
            print(f"❌ Products endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Products endpoint error: {e}")
    
    # Test session endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/session-id/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session endpoint working - Session ID: {data.get('session_id', 'N/A')}")
        else:
            print(f"❌ Session endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Session endpoint error: {e}")

def test_chatbot_endpoint():
    """Test chatbot endpoint"""
    try:
        response = requests.post(
            "http://localhost:8000/api/chatbot",
            json={
                "message": "Hello, can you help me find a good coffee?",
                "session_id": "test_session_123"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chatbot endpoint working - Response: {data.get('reply', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Chatbot endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chatbot endpoint error: {e}")
        return False

def test_frontend_connectivity():
    """Test if frontend can connect to backend"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Testing Coffee AI Integration...")
    print("=" * 50)
    
    # Test backend health
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start the backend first:")
        print("   cd chatbot_rag-main")
        print("   python main.py --port 8000")
        return False
    
    print("\n🔧 Testing API Endpoints...")
    test_api_endpoints()
    
    print("\n🤖 Testing Chatbot...")
    if test_chatbot_endpoint():
        print("✅ Chatbot integration working")
    else:
        print("❌ Chatbot integration failed")
    
    print("\n🎨 Testing Frontend...")
    if test_frontend_connectivity():
        print("✅ Frontend is running")
    else:
        print("❌ Frontend is not running. Please start the frontend:")
        print("   npm run dev")
    
    print("\n" + "=" * 50)
    print("🎉 Integration test completed!")
    print("\n📱 Access your application:")
    print("   Frontend: http://localhost:5173")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    main() 