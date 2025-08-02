#!/usr/bin/env python3
"""
Migration runner script for CAPE-GPT database migrations.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment or construct from parts."""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Construct from Supabase environment variables
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_KEY', '')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Either DATABASE_URL or SUPABASE_URL and SUPABASE_KEY must be set")
    
    # Extract database details from Supabase URL
    # Format: https://project-id.supabase.co
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    # Supabase database connection format
    return f"postgresql://postgres:{supabase_key}@db.{project_id}.supabase.co:5432/postgres"

def run_migration_file(connection, migration_file):
    """Run a single migration file."""
    print(f"Running migration: {migration_file}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    try:
        with connection.cursor() as cursor:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            connection.commit()
            print(f"✅ Migration {migration_file} completed successfully")
            
    except Exception as e:
        connection.rollback()
        print(f"❌ Migration {migration_file} failed: {e}")
        raise

def run_migrations():
    """Run all pending migrations."""
    # Get migrations directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    migrations_dir = os.path.join(project_root, 'supabase', 'migrations')
    
    if not os.path.exists(migrations_dir):
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return False
    
    # Get migration files
    migration_files = []
    for filename in os.listdir(migrations_dir):
        if filename.endswith('.sql'):
            migration_files.append(os.path.join(migrations_dir, filename))
    
    migration_files.sort()  # Run in alphabetical order
    
    if not migration_files:
        print("ℹ️  No migration files found")
        return True
    
    # Connect to database
    try:
        db_url = get_database_url()
        connection = psycopg2.connect(db_url)
        print(f"✅ Connected to database")
        
        # Run migrations
        for migration_file in migration_files:
            run_migration_file(connection, migration_file)
        
        connection.close()
        print(f"🎉 All migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that SUPABASE_URL and SUPABASE_KEY are set correctly in .env")
        print("2. Ensure your Supabase project allows database connections")
        print("3. Verify network connectivity to Supabase")
        return False

def main():
    """Main entry point."""
    print("🚀 CAPE-GPT Database Migration Runner")
    print("=====================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        print("🔍 Dry run mode - showing what would be executed:")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        migrations_dir = os.path.join(project_root, 'supabase', 'migrations')
        
        if os.path.exists(migrations_dir):
            for filename in sorted(os.listdir(migrations_dir)):
                if filename.endswith('.sql'):
                    print(f"  📄 {filename}")
        return
    
    success = run_migrations()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()