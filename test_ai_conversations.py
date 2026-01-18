#!/usr/bin/env python3
"""
Test script for AI Conversation endpoints
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# You need to set this to a valid JWT token
# Get it from the login endpoint or browser dev tools
AUTH_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def test_create_conversation():
    """Test creating a new conversation"""
    print("\n1. Testing conversation creation...")
    
    payload = {
        "title": "Test Conversation",
        "context_type": "general",
        "initial_message": "Xin chào, hãy giới thiệu về Cửu Đỉnh?"
    }
    
    response = requests.post(
        f"{API_BASE}/ai/conversations",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Created conversation: {data['id']}")
        print(f"   Title: {data['title']}")
        return data['id']
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_list_conversations():
    """Test listing conversations"""
    print("\n2. Testing conversation listing...")
    
    response = requests.get(
        f"{API_BASE}/ai/conversations",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} conversations")
        print(f"   Showing {len(data['conversations'])} on this page")
        for conv in data['conversations'][:3]:
            print(f"   - {conv['title']} ({conv['message_count']} messages)")
    else:
        print(f"❌ Error: {response.text}")


def test_get_conversation(conversation_id):
    """Test getting conversation details"""
    print(f"\n3. Testing get conversation {conversation_id}...")
    
    response = requests.get(
        f"{API_BASE}/ai/conversations/{conversation_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved conversation: {data['title']}")
        print(f"   Messages: {len(data['messages'])}")
        for msg in data['messages']:
            print(f"   - [{msg['role']}]: {msg['content'][:50]}...")
    else:
        print(f"❌ Error: {response.text}")


def test_send_message(conversation_id):
    """Test sending a message"""
    print(f"\n4. Testing send message to {conversation_id}...")
    
    payload = {
        "message": "Tôi muốn biết thêm về Đỉnh Thần Công"
    }
    
    response = requests.post(
        f"{API_BASE}/ai/conversations/{conversation_id}/messages",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sent message and received response")
        print(f"   User message: {data['message']['content'][:50]}...")
        print(f"   AI response: {data['response']['content'][:100]}...")
        print(f"   Tokens used: {data['tokens_used']}")
    else:
        print(f"❌ Error: {response.text}")


def test_delete_conversation(conversation_id):
    """Test deleting a conversation"""
    print(f"\n5. Testing delete conversation {conversation_id}...")
    
    response = requests.delete(
        f"{API_BASE}/ai/conversations/{conversation_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✅ Deleted conversation successfully")
    else:
        print(f"❌ Error: {response.text}")


def main():
    print("=" * 60)
    print("AI Conversation Endpoints Test Suite")
    print("=" * 60)
    
    if AUTH_TOKEN == "your_jwt_token_here":
        print("\n⚠️  Please set AUTH_TOKEN in this script first!")
        print("   You can get it from /api/v1/login endpoint")
        sys.exit(1)
    
    # Run tests
    conversation_id = test_create_conversation()
    
    if conversation_id:
        test_list_conversations()
        test_get_conversation(conversation_id)
        test_send_message(conversation_id)
        
        # Optional: uncomment to delete test conversation
        # test_delete_conversation(conversation_id)
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

