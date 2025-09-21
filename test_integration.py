#!/usr/bin/env python3
"""
Test script to verify RAG integration with frontend
"""

import requests
import json
import sys

def test_rag_integration():
    """Test the RAG integration endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing RAG Integration...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/api/tables", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            tables = response.json().get('tables', [])
            print(f"📊 Available tables: {tables}")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure to run: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    # Test 2: Test RAG query endpoint
    test_queries = [
        "How many records are there?",
        "Show me unique values in order_status",
        "What is the distribution of order_status?",
        "Show me sample data from order_request table"
    ]
    
    print("\n🔍 Testing RAG Queries...")
    for query in test_queries:
        try:
            response = requests.post(
                f"{base_url}/api/rag-query",
                json={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Query: '{query}'")
                print(f"   Type: {result.get('type', 'unknown')}")
                print(f"   Message: {result.get('message', 'No message')}")
            else:
                print(f"❌ Query failed: '{query}' - Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Query error: '{query}' - {e}")
    
    # Test 3: Test table data endpoint
    print("\n📋 Testing Table Data Endpoints...")
    for table in tables[:2]:  # Test first 2 tables
        try:
            response = requests.get(f"{base_url}/api/table/{table}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Table '{table}': {data.get('count', 0)} records")
            else:
                print(f"❌ Table '{table}' failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Table '{table}' error: {e}")
    
    print("\n🎉 Integration test completed!")
    print("\nTo start the application:")
    print("1. Make sure you have a .env file with your API keys")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    test_rag_integration()
