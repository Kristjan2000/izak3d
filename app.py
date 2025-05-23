from flask import Flask, render_template, request
import os
import smtplib
from email.message import EmailMessage
import base64
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask import session, redirect, url_for
from flask import flash, get_flashed_messages

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///order.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False

app.secret_key = 'gostilna1515'

db = SQLAlchemy(app)

from datetime import datetime, timedelta, timezone

gmt_plus_2 = timezone(timedelta(hours=2))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drawing_data = db.Column(db.Text)
    description = db.Column(db.Text)
    filename = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(gmt_plus_2))

@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = ""
    if request.method == "POST":
        if request.form ["password"] == "gostilna1515":
            session["logged_in"] = True
            return redirect("/admin")
        else:
            flash("Wrong password, please try again.")
            return redirect("/login")
        
        messages = get_flashed_messages()
        error_message = messages[0] if messages else ""

    return '''
        <form method="post">
            <input type="password" name="password" placeholder="Enter admin password">
            <input type="submit" value="Login">
            <p style="color:red;">{}</p>
        </form>
    '''.format(error_message)



@app.route("/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)

    if order.filename:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], order.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(order)
    db.session.commit()

    return redirect("/admin")



@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return redirect("/login")
    
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    return render_template("admin.html", orders=orders)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/custom")
def custom():
    return render_template("custom.html")

UPLOAD_FOLDER="static/uploads"
ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/submit", methods=["POST"])
def submit():
    description = request.form["description"]
    canvas_image = request.form["canvas_image"]
    email = request.form.get("email", "")
    phone = request.form.get("phone", "")

    file = request.files.get("file")
    filename_secure = None
    file_data = None

    if file and allowed_file(file.filename):
        filename_secure = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"],filename_secure)
        file.save(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

    new_order = Order(
        drawing_data=canvas_image,
        description=description,
        filename=filename_secure,
        email=email,
        phone=phone
    )
    db.session.add(new_order)
    db.session.commit()


    msg = EmailMessage()
    msg["Subject"] = "3D NAROČILO"
    msg["From"] = "kristjanfurlan7@gmail.com"
    msg["To"] = "kristjanfurlan7@gmail.com"

    msg.set_content(f"Description:\n{description}\n\nEmail: {email}\nPhone: {phone}")

    header, encoded = canvas_image.split(",", 1)
    drawing_data = base64.b64decode(encoded)
    msg.add_attachment(drawing_data, maintype="image", subtype="png", filename="drawing.png")

    if file_data:
        msg.add_attachment(file_data, maintype="image", subtype="jpeg", filename = filename_secure)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("kristjanfurlan7@gmail.com", "rbvx nxyr ibqh vsrs")
            smtp.send_message(msg)
        return "Submitted and emailed successfully!"
    except Exception as e:
        return f"Error sending email: {e}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database and table created.")
    app.run(debug=True)
