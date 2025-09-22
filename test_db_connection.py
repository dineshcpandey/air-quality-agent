#!/usr/bin/env python3
"""
Test script to verify database connection using credentials from .env file
"""

import asyncio
import sys
import os

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import DatabaseConnection


async def main():
    """Test database connection and basic functionality"""
    print("🔍 Testing Air Quality Database Connection...")
    print("=" * 50)
    
    # Create database connection (will auto-load from .env)
    db = DatabaseConnection()
    
    try:
        # Test basic connection
        print("1. Testing basic connection...")
        success = await db.test_connection()
        
        if not success:
            print("❌ Basic connection test failed. Check your .env file and database server.")
            return
        
        print("\n2. Testing data sources query...")
        try:
            data_sources = await db.get_data_sources()
            print(f"✅ Found {len(data_sources)} active data sources:")
            
            for source in data_sources[:3]:  # Show first 3
                print(f"   - {source['code']}: {source['name']} ({source['source_type']})")
            
            if len(data_sources) > 3:
                print(f"   ... and {len(data_sources) - 3} more")
                
        except Exception as e:
            print(f"⚠️  Data sources query failed (this is expected if tables don't exist yet): {e}")
        
        print("\n3. Testing a simple system query...")
        try:
            system_info = await db.execute_query("SELECT version() as pg_version")
            print(f"✅ PostgreSQL Version: {system_info[0]['pg_version']}")
            
        except Exception as e:
            print(f"❌ System query failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Database connection test completed!")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        
    finally:
        # Clean up
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())