#!/usr/bin/env python3
"""CLI utility for managing API keys for the Stylize MCP Server."""

import asyncio
import os
import sys
import argparse
import json
from typing import List

# Add current directory to path to import app modules
sys.path.append('.')

from app.auth_service import AuthService
from app.models import APIPermission


class APIKeyManager:
    """CLI manager for API keys."""
    
    def __init__(self):
        """Initialize the API key manager."""
        self.auth_service = AuthService()
    
    async def create_key(self, name: str, permissions: List[str]) -> None:
        """Create a new API key."""
        try:
            # Convert permission strings to enums
            perm_enums = []
            for perm in permissions:
                try:
                    perm_enums.append(APIPermission(perm))
                except ValueError:
                    print(f"❌ Invalid permission: {perm}")
                    print(f"Available permissions: {[p.value for p in APIPermission]}")
                    return
            
            # Create the key
            plain_key, api_key_auth = await self.auth_service.create_and_store_api_key(
                name=name,
                permissions=perm_enums
            )
            
            print(f"✅ Successfully created API key!")
            print(f"Key ID: {api_key_auth.key_id}")
            print(f"Name: {api_key_auth.name}")
            print(f"Permissions: {[p.value for p in api_key_auth.permissions]}")
            print(f"Created: {api_key_auth.created_at}")
            print()
            print(f"🔑 API Key (save this, it won't be shown again):")
            print(f"{plain_key}")
            print()
            print("💡 Usage examples:")
            print(f"  REST API: curl -H 'Authorization: Bearer {plain_key}' ...")
            print(f"  MCP Tool: stylize_image(..., api_key='{plain_key}')")
            
        except Exception as e:
            print(f"❌ Error creating API key: {e}")
    
    async def list_keys(self) -> None:
        """List all API keys."""
        try:
            api_keys = await self.auth_service.list_api_keys()
            
            if not api_keys:
                print("No API keys found.")
                return
            
            print(f"Found {len(api_keys)} API key(s):")
            print()
            
            for key_info in api_keys:
                status = "🟢 Active" if key_info["is_active"] else "🔴 Inactive"
                print(f"📋 {key_info['key_id']} - {key_info['name']}")
                print(f"   Status: {status}")
                print(f"   Permissions: {', '.join(key_info['permissions'])}")
                print(f"   Created: {key_info['created_at']}")
                if key_info['last_used_at']:
                    print(f"   Last used: {key_info['last_used_at']}")
                print(f"   Usage count: {key_info['usage_count']}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing API keys: {e}")
    
    async def deactivate_key(self, key_id: str) -> None:
        """Deactivate an API key."""
        try:
            success = await self.auth_service.deactivate_api_key(key_id)
            
            if success:
                print(f"✅ Successfully deactivated API key: {key_id}")
            else:
                print(f"❌ API key not found: {key_id}")
                
        except Exception as e:
            print(f"❌ Error deactivating API key: {e}")
    
    async def update_key(self, key_id: str, is_active: bool = None, permissions: List[str] = None) -> None:
        """Update an API key."""
        try:
            perm_enums = None
            if permissions:
                perm_enums = []
                for perm in permissions:
                    try:
                        perm_enums.append(APIPermission(perm))
                    except ValueError:
                        print(f"❌ Invalid permission: {perm}")
                        print(f"Available permissions: {[p.value for p in APIPermission]}")
                        return
            
            success = await self.auth_service.update_api_key(
                key_id=key_id,
                is_active=is_active,
                permissions=perm_enums
            )
            
            if success:
                print(f"✅ Successfully updated API key: {key_id}")
            else:
                print(f"❌ API key not found: {key_id}")
                
        except Exception as e:
            print(f"❌ Error updating API key: {e}")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Manage API keys for Stylize MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create key command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("name", help="Human-readable name for the key")
    create_parser.add_argument(
        "--permissions", 
        nargs="+", 
        default=["stylize", "styles"],
        help="Permissions to grant (default: stylize styles)"
    )
    
    # List keys command
    list_parser = subparsers.add_parser("list", help="List all API keys")
    
    # Deactivate key command
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate an API key")
    deactivate_parser.add_argument("key_id", help="ID of the key to deactivate")
    
    # Update key command
    update_parser = subparsers.add_parser("update", help="Update an API key")
    update_parser.add_argument("key_id", help="ID of the key to update")
    update_parser.add_argument("--active", type=bool, help="Set active status (true/false)")
    update_parser.add_argument("--permissions", nargs="+", help="New permissions")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show available permissions and configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle info command separately
    if args.command == "info":
        print("🔐 Stylize MCP Server - API Key Management")
        print("=" * 50)
        print()
        print("Available Permissions:")
        for perm in APIPermission:
            print(f"  - {perm.value}")
        print()
        print("Environment Variables:")
        print(f"  AUTH_ENABLED: {os.environ.get('AUTH_ENABLED', 'true')}")
        print(f"  AUTH_DEV_BYPASS: {os.environ.get('AUTH_DEV_BYPASS', 'false')}")
        print(f"  GCP_PROJECT_ID: {'✅' if os.environ.get('GCP_PROJECT_ID') else '❌'}")
        print(f"  API_KEYS_SECRET_PATH: {os.environ.get('API_KEYS_SECRET_PATH', 'api-keys')}")
        print()
        print("Usage Examples:")
        print("  python manage_api_keys.py create 'Production Client' --permissions stylize styles mcp")
        print("  python manage_api_keys.py list")
        print("  python manage_api_keys.py deactivate key-abc123")
        print("  python manage_api_keys.py update key-abc123 --active false")
        return
    
    # Initialize manager and run command
    manager = APIKeyManager()
    
    try:
        if args.command == "create":
            await manager.create_key(args.name, args.permissions)
        elif args.command == "list":
            await manager.list_keys()
        elif args.command == "deactivate":
            await manager.deactivate_key(args.key_id)
        elif args.command == "update":
            await manager.update_key(
                args.key_id,
                is_active=args.active,
                permissions=args.permissions
            )
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())