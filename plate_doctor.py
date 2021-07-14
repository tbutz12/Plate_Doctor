import json, time
from flask import Flask, request, abort, url_for, redirect, session, render_template, flash
from models import db, User
from datetime import datetime
from sqlalchemy import exc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Plate_Doctor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

users = {}

@app.route("/")
def default():
    return redirect(url_for("login"))

@app.route("/login/", methods=["GET", "POST"])
def login():
    result = User.query.all()
    if request.method == "POST":
        for r in result:
            if r.username == request.form["user"] and r.password == request.form["pass"]:
                session["username"] = r.username
                userName = r.username
                if(userName not in users):
                    users[userName] = r.password
                return redirect(url_for("homepage", username=r.username)) 
    return render_template("login.html")

@app.route("/homepage/<username>", methods=["GET", "POST"])
def homepage(username=None):
    if not username:
        return redirect(url_for("login"))
    else:
        return render_template("homepage.html")

@app.route("/registration/", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        userName = request.form["user"]
        qUser = User.query.all()
        for u in qUser:
            users[u.username] = u.password
        if(userName in users):
            return redirect(url_for("registration"))
        users[userName] = request.form["pass"]
        if(len(userName) == 0):
            return render_template("registration.html")
        passW = request.form["pass"]
        if(len(passW) == 0):
            return render_template("registration.html")
        q = User(userName, passW)
        db.session.add(q)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("registration.html")

@app.route("/logout/")
def logout():
    if "username" in session:
        session.clear()
        return render_template("logoutPage.html")
    else:
        return redirect(url_for("login"))

# with open("recipes_raw_nosource_epi.json") as f:
#     data = json.load(f)
    
# val = input("Enter a recipe to search for: ")
# start_time = time.time()
# for key, value in data.items():
#     if val.lower() in value['title'].lower():
#         print(value['title'])

app.secret_key = "asdf;lkj"
            
if __name__ == "__main__":
    app.run()





