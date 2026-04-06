import sys
import os

# Point to your project directory
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# Import your Flask app
from app import app as application