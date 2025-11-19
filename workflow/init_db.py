# init_db.py
from db import Base, engine
import model # ensure models are imported so they are registered with Base

Base.metadata.create_all(bind=engine)
print("Database and tables created/updated.")
