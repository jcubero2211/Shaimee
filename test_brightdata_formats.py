#!/usr/bin/env python3
"""
Bright Data Proxy Format Tester
Tests different authentication formats to find the working one
"""

import asyncio
import aiohttp
import os
import random
from dotenv import load_dotenv

async def test_proxy_formats():
    """Test different Bright Data proxy formats"""
    load_dotenv()
    
    proxy_host = os.getenv('PROXY_HOST')
    proxy_port = os.getenv('PROXY_PORT')
    proxy_user = os.getenv('PROXY_USER')
    proxy_pass = os.getenv('PROXY_PASS')
    
    print(f"🔧 Testing Bright Data proxy formats...")
    print(f"Host: {proxy_host}:{proxy_port}")
    print(f"Base user: {proxy_user[:30]}...")
    print()
    
    # Different formats to try
    session_id = random.randint(100000, 999999)
    
    formats_to_test = [
        # Original format
        {
            'name': 'Original',
            'user': proxy_user,
            'description': 'Basic credentials as provided'
        },
        # With session
        {
            'name': 'With Session',
            'user': f"{proxy_user}-session-{session_id}",
            'description': 'Added random session ID'
        },
        # With Costa Rica country
        {
            'name': 'Costa Rica Country',
            'user': f"{proxy_user}-country-cr",
            'description': 'Costa Rica country targeting'
        },
        # With both session and country
        {
            'name': 'CR + Session',
            'user': f"{proxy_user}-country-cr-session-{session_id}",
            'description': 'Costa Rica + session ID'
        },
        # Alternative session format
        {
            'name': 'Alt Session Format',
            'user': f"{proxy_user}_session-{session_id}",
            'description': 'Alternative session format with underscore'
        },
        # Zone format (some Bright Data accounts use this)
        {
            'name': 'Zone Format',
            'user': proxy_user.replace('zone-residential_proxy1', 'zone-residential'),
            'description': 'Simplified zone name'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    successful_format = None
    
    for format_test in formats_to_test:
        proxy_url = f"http://{format_test['user']}:{proxy_pass}@{proxy_host}:{proxy_port}"
        
        print(f"🧪 Testing: {format_test['name']}")
        print(f"   Description: {format_test['description']}")
        print(f"   User format: {format_test['user'][:50]}...")
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Test with a simple IP checker first
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy_url,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    
                    print(f"   📡 Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get('origin', 'unknown')
                        print(f"   ✅ SUCCESS! IP: {ip}")
                        
                        # Test if it's actually from Costa Rica
                        # (IP geolocation would show this, but we'll assume it worked)
                        successful_format = format_test
                        break
                    elif response.status == 407:
                        print(f"   ❌ Auth failed (407)")
                    else:
                        print(f"   ⚠️  Unexpected status: {response.status}")
                        
        except Exception as e:
            print(f"   💥 Error: {str(e)[:50]}...")
        
        print()
        await asyncio.sleep(1)  # Be nice to the server
    
    if successful_format:
        print(f"🎉 FOUND WORKING FORMAT: {successful_format['name']}")
        print(f"💡 Use this user format: {successful_format['user']}")
        print(f"🔧 Full proxy URL format:")
        print(f"   http://{successful_format['user']}:YOUR_PASSWORD@{proxy_host}:{proxy_port}")
    else:
        print("😞 No working format found.")
        print("🔧 Recommendations:")
        print("   1. Check your Bright Data dashboard for the exact format")
        print("   2. Verify your zone name is correct")
        print("   3. Ensure your account has residential proxy access")
        print("   4. Contact Bright Data support with the 407 error")

if __name__ == "__main__":
    asyncio.run(test_proxy_formats())
