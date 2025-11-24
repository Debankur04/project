import sys
import os

# Add project root so "workflow" can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# init_db.py
# workflow/init_db.py

from workflow.db import Base, engine
from workflow import model  # <-- IMPORTANT: import model file so tables register

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
