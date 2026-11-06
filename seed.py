"""
Optional: run once to add some sample categories.
    python seed.py
"""
from app import app
from models import Category, db

SAMPLE_CATEGORIES = [
    ("Housing", 1200.0),
    ("Food", 400.0),
    ("Transport", 200.0),
    ("Entertainment", 150.0),
    ("Utilities", 250.0),
]

with app.app_context():
    for name, budget in SAMPLE_CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, budget_limit=budget))
    db.session.commit()
    print("Sample categories added.")
