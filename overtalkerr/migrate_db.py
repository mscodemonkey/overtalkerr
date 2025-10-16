#!/usr/bin/env python3
"""
Database migration script for adding timestamp columns to existing database.

This script safely migrates an existing database to the new schema with
created_at and updated_at columns.
"""
import os
import sys
import datetime as dt
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./overtalkerr.db")


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Run database migration"""
    print(f"🔄 Starting database migration...")
    print(f"📊 Database: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if table exists
        inspector = inspect(engine)
        if 'session_state' not in inspector.get_table_names():
            print("❌ Table 'session_state' does not exist. Run db.py to create tables first.")
            return False

        # Check if created_at column exists
        if check_column_exists(engine, 'session_state', 'created_at'):
            print("✅ Migration already complete - created_at column exists")
            return True

        print("📝 Adding timestamp columns to session_state table...")

        try:
            # SQLite-specific migration (ALTER TABLE is limited in SQLite)
            if DATABASE_URL.startswith("sqlite"):
                print("   Detected SQLite database - using SQLite migration strategy")

                # Add created_at column with default
                conn.execute(text("""
                    ALTER TABLE session_state
                    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()

                # Add updated_at column with default
                conn.execute(text("""
                    ALTER TABLE session_state
                    ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()

                # Create indexes
                print("   Creating indexes...")
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_session_user_conv
                        ON session_state (user_id, conversation_id)
                    """))
                    conn.commit()
                except Exception as e:
                    print(f"   ⚠️  Index ix_session_user_conv might already exist: {e}")

                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_session_created
                        ON session_state (created_at)
                    """))
                    conn.commit()
                except Exception as e:
                    print(f"   ⚠️  Index ix_session_created might already exist: {e}")

            # PostgreSQL/MySQL migration
            else:
                print("   Detected non-SQLite database - using standard SQL migration")

                # Add created_at column
                conn.execute(text("""
                    ALTER TABLE session_state
                    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT NOW()
                """))
                conn.commit()

                # Add updated_at column
                conn.execute(text("""
                    ALTER TABLE session_state
                    ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                """))
                conn.commit()

                # Create indexes
                print("   Creating indexes...")
                conn.execute(text("""
                    CREATE INDEX ix_session_user_conv
                    ON session_state (user_id, conversation_id)
                """))
                conn.commit()

                conn.execute(text("""
                    CREATE INDEX ix_session_created
                    ON session_state (created_at)
                """))
                conn.commit()

            print("✅ Migration completed successfully!")
            print(f"   - Added created_at column")
            print(f"   - Added updated_at column")
            print(f"   - Created composite index on (user_id, conversation_id)")
            print(f"   - Created index on created_at")

            # Show record count
            result = conn.execute(text("SELECT COUNT(*) FROM session_state"))
            count = result.scalar()
            print(f"\n📊 Total records migrated: {count}")

            return True

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print(f"\nError details: {type(e).__name__}: {str(e)}")
            conn.rollback()
            return False


def verify_migration():
    """Verify that the migration was successful"""
    print("\n🔍 Verifying migration...")

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    try:
        columns = {col['name']: col for col in inspector.get_columns('session_state')}

        required_columns = ['id', 'user_id', 'conversation_id', 'state_json', 'created_at', 'updated_at']
        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"❌ Verification failed - missing columns: {missing}")
            return False

        print("✅ All required columns present:")
        for col in required_columns:
            col_info = columns[col]
            print(f"   - {col}: {col_info.get('type', 'unknown')}")

        # Check indexes
        indexes = inspector.get_indexes('session_state')
        print("\n✅ Indexes:")
        for idx in indexes:
            print(f"   - {idx['name']}: {idx['column_names']}")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  Alexa Overseerr Database Migration")
    print("=" * 60)

    success = migrate()

    if success:
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
