from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
app = Flask(__name__)

app.secret_key = "barishal_mach_ghor_secret"

serializer = URLSafeTimedSerializer(app.secret_key)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

def generate_reset_token(email):
    return serializer.dumps(email, salt="reset-password")


def verify_reset_token(token, expires_sec=1800):
    try:
        email = serializer.loads(
            token,
            salt="reset-password",
            max_age=expires_sec
        )
        return email
    except Exception:
        return None

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fish.db"

db = SQLAlchemy(app)


class Fish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(20), default="super_admin")

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

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            session["admin"] = True
            session["admin_id"] = admin.id
            return redirect("/dashboard")

        return "ভুল Username অথবা Password"

    return render_template("admin/login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email").strip().lower()

        print("EMAIL RECEIVED:", email)

        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            return "এই Gmail দিয়ে কোনো Admin পাওয়া যায়নি"

        token = generate_reset_token(admin.email)

        reset_link = url_for(
            "reset_password",
            token=token,
            _external=True
        )

        msg = Message(
            "Barishal Mach Ghor - Password Reset",
            recipients=[admin.email]
        )

        msg.body = f"""
আসসালামু আলাইকুম,

আপনার Password Reset করার অনুরোধ পাওয়া গেছে।

নিচের লিংকে ক্লিক করুন:

{reset_link}

যদি আপনি এই অনুরোধ না করে থাকেন, তাহলে এই ইমেইলটি উপেক্ষা করুন।
"""

        print("MAIL_USERNAME =", app.config["MAIL_USERNAME"])
        mail.send(msg)

        return "আপনার Gmail-এ Password Reset Link পাঠানো হয়েছে।"

    return render_template("admin/forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    email = verify_reset_token(token)

    if not email:
        return "এই Reset Linkটি অবৈধ বা মেয়াদ শেষ হয়ে গেছে।"

    admin = Admin.query.filter_by(email=email).first()

    if not admin:
        return "Admin পাওয়া যায়নি"

    if request.method == "POST":

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            return "দুটি Password এক নয়"

        admin.password = new_password
        db.session.commit()

        return redirect("/admin")

    return render_template("admin/reset_password.html")

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
