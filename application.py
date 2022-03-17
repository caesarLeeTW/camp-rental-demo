from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import ntd, login_required, apology

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["ntd"] = ntd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///rental.db")

@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT * FROM equipments")
    return render_template("index.html", equipments=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pwd_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route vie GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure email was submitted
        elif not request.form.get("email"):
            return apology("must provide email", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password double check was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password again", 400)

        # Ensure password was submitted
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("two passwords not the same", 400)

        # Ensure not username not duplicated
        rows = db.execute("SELECT * FROM users WHERE name = ?", request.form.get("username"))
        if len(rows) > 0:
            return apology("username is taken", 400)

        password_hash = generate_password_hash(request.form.get("password"))
        id = db.execute("INSERT INTO users (name, pwd_hash, email) VALUES (?, ?, ?)", request.form.get("username"), password_hash, request.form.get("email"))

        # Remember which user has logged in
        session["user_id"] = id

        return redirect("/")

    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")


@app.route("/rent", methods=["POST"])
@login_required
def rent():
    equipment_id = request.form.get("equipment-id")
    count = request.form.get("count")
    print(f"count = {count}")
    if not count.isnumeric():
        return apology("must select count", 403)
    count = int(count)

    rows = db.execute("SELECT * FROM equipments WHERE id = ?", equipment_id)
    if len(rows) == 0:
        print(f"equipment id ${equipment_id} is missing!")
        return apology("unknown error")
    
    equipment = rows[0]
    if equipment['remain_count'] == 0:
        return apology(f"{equipment['title']} has run out of stock", 400)
    elif equipment['remain_count'] < count:
        return apology(f"There are only {equipment['remain_count']} left for {equipment['title']} ")

    total_price = count * equipment['price']
    # new transaction
    transaction_id = db.execute("INSERT INTO transactions (user_id, total_price, timestamp) VALUES(?, ?, ?)", session["user_id"], total_price, datetime.datetime.now().timestamp())
    # new transaction detail
    db.execute("INSERT INTO transaction_details (transaction_id, equipment_id, count, unit_price) VALUES(?, ?, ?, ?)", transaction_id, equipment_id, count, equipment['price'])
    # modify equipment remain_count
    remain_count = equipment['remain_count'] - count
    db.execute("UPDATE equipments SET remain_count = ? WHERE id = ?", remain_count, equipment_id)
    # 
    rows = db.execute("SELECT * FROM renting_items WHERE user_id = ? AND equipment_id = ?", session["user_id"], equipment_id)
    if len(rows) == 0:
        db.execute("INSERT INTO renting_items (user_id, equipment_id, count) VALUES(?, ?, ?)", session["user_id"], equipment_id, count)
    else:
        renting_count = rows[0]["count"] + count
        db.execute("UPDATE renting_items SET count = ? WHERE user_id = ? AND equipment_id = ?", renting_count, session["user_id"], equipment_id)
    return redirect('/rental')


@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT title, count, total_price, timestamp FROM transactions JOIN transaction_details ON transactions.id = transaction_details.transaction_id JOIN equipments ON transaction_details.equipment_id = equipments.id WHERE user_id = ?;", session["user_id"])
    transactions = []
    for row in rows:
        transactions.append({
            "equipment": row["title"],
            "count": row["count"],
            "price": row["total_price"],
            "time": datetime.datetime.fromtimestamp(row["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    return render_template("history.html", transactions=transactions)


@app.route("/rental")
@login_required
def rental():
    rows = db.execute("SELECT * FROM renting_items JOIN equipments ON renting_items.equipment_id = equipments.id WHERE user_id = ?", session["user_id"])
    rentals = []
    for row in rows:
        rentals.append({
            "equipment": row["title"],
            "count": row["count"],
            "price": row["price"] * row["count"],
        })
    return render_template("rental.html", rentals=rentals)

