import sys
import os
from alembic.config import Config
from alembic import command

def run_migrations():
    # Ensure current directory is in path
    sys.path.append(os.getcwd())
    
    # Load the alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Run the upgrade command
    print("Running migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully.")

if __name__ == "__main__":
    run_migrations()
