#!/usr/bin/env python3
"""Test script for WXAuto channel."""

import asyncio
import sys
from pathlib import Path

# Add nanobot to path
sys.path.insert(0, str(Path(__file__).parent))

from nanobot.channels.wxauto import WXAutoChannel, WXAutoAPI
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import WXAutoConfig


async def test_wxauto_api():
    """Test WXAuto API client."""
    print("Testing WXAuto API client...")
    
    # Create a mock API client
    api = WXAutoAPI(
        api_url="http://localhost:8080",
        api_key="test_key",
        wxname="test_wx"
    )
    
    print(f"API URL: {api.api_url}")
    print(f"API Key: {api.api_key[:10]}...")
    print(f"WXName: {api.wxname}")
    
    # Test is_online (this will fail if no server is running, but that's OK)
    print("\nTesting is_online...")
    result = api.is_online()
    print(f"Success: {result.get('success')}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        print("(This is expected if WXAuto server is not running)")
    
    return True


async def test_wxauto_channel():
    """Test WXAuto channel initialization."""
    print("\nTesting WXAuto channel...")
    
    # Create config
    config = WXAutoConfig(
        enabled=True,
        api_url="http://localhost:8080",
        api_key="test_key",
        wxname="test_wx",
        poll_interval=3,
        allow_from=["*"],
        group_policy="open"
    )
    
    # Create message bus
    bus = MessageBus()
    
    # Create channel
    channel = WXAutoChannel(config, bus)
    
    print(f"Channel name: {channel.name}")
    print(f"Config enabled: {config.enabled}")
    print(f"API URL: {config.api_url}")
    print(f"Poll interval: {config.poll_interval}s")
    
    # Test is_allowed
    print("\nTesting is_allowed...")
    print(f"  '*' allowed: {channel.is_allowed('*')}")
    print(f"  'wxauto:文件传输助手' allowed: {channel.is_allowed('wxauto:文件传输助手')}")
    print(f"  'wxauto:test_chat' allowed: {channel.is_allowed('wxauto:test_chat')}")
    
    # Test with specific allow list
    config.allow_from = ["文件传输助手", "王旭"]
    channel2 = WXAutoChannel(config, bus)
    print(f"\nWith allow_from=['文件传输助手', '王旭']:")
    print(f"  'wxauto:文件传输助手' allowed: {channel2.is_allowed('wxauto:文件传输助手')}")
    print(f"  'wxauto:王旭' allowed: {channel2.is_allowed('wxauto:王旭')}")
    print(f"  'wxauto:其他人' allowed: {channel2.is_allowed('wxauto:其他人')}")
    
    return True


async def main():
    """Main test function."""
    print("=" * 60)
    print("Testing WXAuto Channel Implementation")
    print("=" * 60)
    
    try:
        # Test API client
        await test_wxauto_api()
        
        # Test channel
        await test_wxauto_channel()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update test_wxauto_config.json with your actual API credentials")
        print("2. Start WXAuto server (if not already running)")
        print("3. Run: nanobot gateway -c test_wxauto_config.json")
        print("4. Send a message to '文件传输助手' via WeChat")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)