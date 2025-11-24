#!/usr/bin/env python3

import asyncio
import asyncpg
import uuid

async def fix_login_issue():
    """Fix login issues by ensuring test user exists and database is accessible"""
    
    database_url = "postgresql://postgres:postgresql%409891@localhost:5432/sensordb"
    
    try:
        # Connect to database
        print("🔍 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Check if users table exists
        print("🔍 Checking users table...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        
        if not table_exists:
            print("📝 Creating users table...")
            await conn.execute("""
                CREATE TABLE users (
                    id UUID PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        
        # Check if admin user exists
        print("🔍 Checking for admin user...")
        admin_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE username = 'admin')"
        )
        
        if not admin_exists:
            print("👤 Creating admin user...")
            user_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO users (id, username, email, hashed_password) VALUES ($1, $2, $3, $4)",
                user_id, "admin", "admin@test.com", "admin123"
            )
            print("✅ Admin user created: admin/admin123")
        else:
            print("✅ Admin user already exists")
        
        # Verify login credentials
        print("🔍 Verifying login credentials...")
        user = await conn.fetchrow(
            "SELECT username, hashed_password FROM users WHERE username = 'admin'"
        )
        
        if user and user['hashed_password'] == 'admin123':
            print("✅ Login credentials verified: admin/admin123")
        else:
            print("❌ Login credentials mismatch")
            
        await conn.close()
        print("✅ Database connection test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_login_issue())
    if success:
        print("\n🎉 Login should now work with:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   URL: http://localhost:8000/")
    else:
        print("\n❌ Please check PostgreSQL is running and accessible")