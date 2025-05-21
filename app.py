from flask import Flask, render_template, request
import os
import smtplib
from email.message import EmailMessage
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)

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

    file = request.files.get("file")
    file_data = file.read() if file else None
    file_name = file.filename if file else None

    msg = EmailMessage()
    msg["Subject"] = "3D NAROČILO"
    msg["From"] = "kristjanfurlan7@gmail.com"
    msg["To"] = "kristjanfurlan7@gmail.com"

    msg.set_content(f"Description:\n{description}")

    header, encoded = canvas_image.split(",", 1)
    drawing_data = base64.b64decode(encoded)
    msg.add_attachment(drawing_data, maintype="image", subtype="png", filename="drawing.png")

    if file_data:
        msg.add_attachment(file_data, maintype="image", subtype="jpeg", filename = file_name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("kristjanfurlan7@gmail.com", "rbvx nxyr ibqh vsrs")
            smtp.send_message(msg)
        return "Submitted and emailed successfully!"
    except Exception as e:
        return f"Error sending email: {e}"

if __name__ == "__main__":
    app.run(debug=True)
