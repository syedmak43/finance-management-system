import os
from datetime import date

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func

from models import Category, Expense, db

app = Flask(__name__)

# Set DATABASE_URL to a SQLAlchemy-compatible database URL.
# You can override this with an environment variable called DATABASE_URL.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://root@localhost/expense_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# The secret key is needed for flash messages (small notifications after a form submit)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")

db.init_app(app)

# Create the tables in MySQL if they don't exist yet
with app.app_context():
    db.create_all()


def spending_per_category():
    """
    Return every category with the total amount spent in it.
    Uses a LEFT OUTER JOIN so categories with no expenses still appear (with 0 spent).
    """
    return (
        db.session.query(
            Category.id,
            Category.name,
            Category.budget_limit,
            func.coalesce(func.sum(Expense.amount), 0).label("spent"),
        )
        .outerjoin(Expense, Expense.category_id == Category.id)
        .group_by(Category.id, Category.name, Category.budget_limit)
        .order_by(Category.name)
        .all()
    )


# ---------- Pages ----------

@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    summary = []
    for row in spending_per_category():
        spent = float(row.spent)
        budget = row.budget_limit
        percent = (spent / budget * 100) if budget > 0 else 0
        summary.append({
            "id": row.id,
            "name": row.name,
            "budget": budget,
            "spent": spent,
            "over": spent > budget,
            "bar": min(percent, 100),  # progress bar never goes past 100%
        })

    total_budget = sum(item["budget"] for item in summary)
    total_spent = sum(item["spent"] for item in summary)

    recent_expenses = (
        Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).limit(10).all()
    )

    return render_template(
        "dashboard.html",
        summary=summary,
        total_budget=total_budget,
        total_spent=total_spent,
        total_remaining=total_budget - total_spent,
        recent_expenses=recent_expenses,
    )


@app.route("/expense/add", methods=["GET"])
def add_expense():
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "add_expense.html", categories=categories, today=date.today().isoformat()
    )


# ---------- Form handlers ----------

@app.route("/expense/add", methods=["POST"])
def save_expense():
    # 1. Read the form values
    amount_text = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    category_id = request.form.get("category_id", type=int)
    date_text = request.form.get("date", "").strip()

    # 2. Validate the amount
    try:
        amount = float(amount_text)
    except ValueError:
        flash("Amount must be a number.", "error")
        return redirect(url_for("add_expense"))
    if amount <= 0:
        flash("Amount must be greater than zero.", "error")
        return redirect(url_for("add_expense"))

    # 3. Validate the description
    if not description or len(description) > 200:
        flash("Description is required and must be 200 characters or fewer.", "error")
        return redirect(url_for("add_expense"))

    # 4. Check the foreign key: the category must exist
    category = db.session.get(Category, category_id) if category_id else None
    if category is None:
        flash("Please choose a valid category.", "error")
        return redirect(url_for("add_expense"))

    # 5. Validate the date (uses today's date if the field is empty)
    try:
        expense_date = date.fromisoformat(date_text) if date_text else date.today()
    except ValueError:
        flash("Date is not valid.", "error")
        return redirect(url_for("add_expense"))

    # 6. Create the record and save it to MySQL
    expense = Expense(
        amount=amount,
        description=description,
        date=expense_date,
        category_id=category.id,
    )
    db.session.add(expense)
    db.session.commit()

    flash(f"Saved ${amount:.2f} for {description}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/category/add", methods=["POST"])
def add_category():
    name = request.form.get("name", "").strip()
    budget_text = request.form.get("budget_limit", "").strip()

    if not name or len(name) > 50:
        flash("Category name is required and must be 50 characters or fewer.", "error")
        return redirect(url_for("add_expense"))

    try:
        budget = float(budget_text)
    except ValueError:
        flash("Budget limit must be a number.", "error")
        return redirect(url_for("add_expense"))
    if budget < 0:
        flash("Budget limit cannot be negative.", "error")
        return redirect(url_for("add_expense"))

    # The name column is unique, so check for duplicates first
    if Category.query.filter_by(name=name).first():
        flash(f"A category named '{name}' already exists.", "error")
        return redirect(url_for("add_expense"))

    db.session.add(Category(name=name, budget_limit=budget))
    db.session.commit()

    flash(f"Category '{name}' created.", "success")
    return redirect(url_for("add_expense"))


@app.route("/category/<int:category_id>/add-funds", methods=["POST"])
def add_funds(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        flash("Category not found.", "error")
        return redirect(url_for("dashboard"))

    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        flash("Amount must be a number.", "error")
        return redirect(url_for("dashboard"))
    if amount <= 0:
        flash("Amount must be greater than zero.", "error")
        return redirect(url_for("dashboard"))

    category.budget_limit += amount
    db.session.commit()

    flash(f"Added ${amount:.2f} to {category.name}.", "success")
    return redirect(url_for("dashboard"))


# ---------- JSON API used by the chart ----------

@app.route("/api/chart-data")
def chart_data():
    rows = spending_per_category()
    return jsonify({
        "labels": [row.name for row in rows],
        "data": [float(row.spent) for row in rows],
    })


if __name__ == "__main__":
    app.run(debug=True)
