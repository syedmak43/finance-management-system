from datetime import date

from flask_sqlalchemy import SQLAlchemy

# This object connects our tables to the database. It is created here
# and attached to the Flask app inside app.py.
db = SQLAlchemy()


class Category(db.Model):
    """A budget category such as Housing or Food. One category has many expenses."""

    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    budget_limit = db.Column(db.Float, nullable=False)

    # Lets us write category.expenses to get a list of its expenses
    expenses = db.relationship(
        "Expense", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category {self.name}>"


class Expense(db.Model):
    """A single spending transaction that belongs to one category."""

    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, default=date.today)

    # Foreign key: this value must match an id in the category table
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    # Lets us write expense.category to get the Category object
    category = db.relationship("Category", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.description} {self.amount}>"
