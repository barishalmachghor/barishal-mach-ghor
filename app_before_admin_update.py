from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "barishal_mach_ghor_secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fish.db"

db = SQLAlchemy(app)


class Fish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    fish_id = db.Column(db.Integer, db.ForeignKey("fish.id"))
    fish = db.relationship("Fish")

    quantity = db.Column(db.Integer)
    status = db.Column(db.String(20), default="Pending")



@app.route("/")
def home():
    search = request.args.get("search", "")

    if search:
        fishes = Fish.query.filter(
            Fish.name.ilike(f"%{search}%")
        ).all()
    else:
        fishes = Fish.query.all()

    return render_template(
        "index.html",
        fishes=fishes,
        search=search
    )

@app.route("/place_order", methods=["POST"])
def place_order():

    order = Order(
        customer_name=request.form.get("name"),
        phone=request.form.get("phone"),
        address=request.form.get("address"),
        fish_id=request.form.get("fish_id"),
        quantity=request.form.get("quantity")
    )

    db.session.add(order)
    db.session.commit()

    return "অর্ডার সফলভাবে গ্রহণ করা হয়েছে"

@app.route("/order")
def order():
    fishes = Fish.query.all()
    return render_template("order.html", fishes=fishes)


# Admin Login
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "12345":
            session["admin"] = True
            return redirect("/dashboard")

        return "ভুল Username অথবা Password"

    return render_template("admin/login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    fishes = Fish.query.all()
    total_fish = len(fishes)
    return render_template(
        "admin/dashboard.html",
        fishes=fishes,
        total_fish=total_fish)

# Orders
@app.route("/orders")
def orders():

    if not session.get("admin"):
        return redirect("/admin")

    orders = Order.query.all()

    return render_template(
        "admin/orders.html",
        orders=orders
    )

# Add Fish
@app.route("/add_fish", methods=["GET", "POST"])
def add_fish():

    if not session.get("admin"):
        return redirect("/admin")

    if request.method == "POST":

        fish = Fish(
            name=request.form.get("name"),
            price=request.form.get("price"),
            stock=request.form.get("stock"),
            image=request.form.get("image")
        )

        db.session.add(fish)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("admin/add_fish.html")


# Edit Fish
@app.route("/edit_fish/<int:id>", methods=["GET", "POST"])
def edit_fish(id):

    if not session.get("admin"):
        return redirect("/admin")

    fish = Fish.query.get_or_404(id)

    if request.method == "POST":

        fish.name = request.form.get("name")
        fish.price = request.form.get("price")
        fish.stock = request.form.get("stock")
        fish.image = request.form.get("image")

        db.session.commit()

        return redirect("/dashboard")

    return render_template(
        "admin/edit_fish.html",
        fish=fish
    )
# Delete Fish
@app.route("/delete_fish/<int:id>")
def delete_fish(id):

    if not session.get("admin"):
        return redirect("/admin")

    fish = Fish.query.get_or_404(id)

    db.session.delete(fish)
    db.session.commit()

    return redirect("/dashboard")# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")


with app.app_context():
    db.create_all()


app.run(host="0.0.0.0", port=5000, debug=True)
