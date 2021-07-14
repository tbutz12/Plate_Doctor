import json, urllib.parse
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
recipe_list = []

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
        if request.method == "POST":
            val = request.form["recipe"] 
            return redirect(url_for("recipes", value = val))
        else:
            return render_template("homepage.html")

@app.route("/recipe/<value>", methods =["GET", "POST"])
def recipes(value=None):
    if not value:
        return render_template("homepage.html", username = session["username"])
    else:
        if request.method == "POST":
            recipe_name = request.form["viewRecipe"] 
            return redirect(url_for("recipe_name", recipe = recipe_name))
        r = findRecipe(value)
        return render_template("recipe.html", list = r)

@app.route("/recipe_name/<recipe>", methods =["GET", "POST"])
def recipe_name(recipe=None):
    if not recipe:
        return render_template("homepage.html", username = session["username"])
    else:
        if request.method == "POST":
            render_template("homepage.html", username = session["username"])
        recipe_uni = urllib.parse.unquote(recipe)
        r = showRecipe(recipe_uni)
        return render_template("recipe_name.html", list = r)

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

def findRecipe(val):
    data = []
    with open("recipes_raw_nosource_epi.json") as f:
        data = json.load(f)
    for key, value in data.items():
        if val.lower() in value['title'].lower():
            recipe_list.append(value['title'])
    return recipe_list

def showRecipe(recipe):
    data = []
    with open("recipes_raw_nosource_epi.json") as f:
        data = json.load(f)
    recipe_name_list = []
    for key, value in data.items():
        if recipe.lower() in value['title'].lower():
            recipe_name_list.append("Recipe Name")
            recipe_name_list.append(value['title'])
            recipe_name_list.append("Ingredients")
            recipe_name_list.append(value['ingredients'])
            recipe_name_list.append("Instructions")
            recipe_name_list.append(value['instructions'])
    return recipe_name_list

app.secret_key = "asdf;lkj"
            
if __name__ == "__main__":
    app.run()





