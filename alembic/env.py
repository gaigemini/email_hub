from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- FIX 1: Load .env file ---
from dotenv import load_dotenv
load_dotenv()
import os
# --- End Fix 1 ---

# --- FIX 2: Import your Base model ---
# Add this line to import your Base from models.py
# Make sure models.py is reachable (it should be, from the root)
import sys
sys.path.append(os.getcwd()) # Add project root to Python path
from models import Base
# --- End Fix 2 ---


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- FIX 3: Set target_metadata ---
# Set this to your Base's metadata
target_metadata = Base.metadata
# --- End Fix 3 ---

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Helper to get the database URL from the environment."""
    return os.getenv("DATABASE_URL")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url() # Use helper
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    
    # Get the database URL from our helper
    db_url = get_url()
    
    # Create a configuration dictionary for engine_from_config
    # This prevents the "config_main_option" error
    # We are bypassing the .ini file's URL and using our env var
    connectable_config = config.get_section(config.config_ini_section, {})
    connectable_config["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        connectable_config, # Use our constructed config
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

