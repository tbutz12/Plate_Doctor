import json, urllib.parse
from flask import Flask, request, abort, url_for, redirect, session, render_template, flash
#from sqlalchemy.ext.declarative.api import declarative_base
from models import db, User, User_Favorited_Recipes
from datetime import datetime
from sqlalchemy import exc

app = Flask(__name__)
app.run(debug=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Plate_Doctor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#list of special characters that are not allowed in usernames
special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "+", "=", "[", "]", "{", "}", "|", ":", ";", "'", '"', ",", "<", ".", ">", "/", "?", "~", "`", " "]

with app.app_context():
	#drop all pre-existing tables
	db.drop_all()
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
			if r.username == request.form["user"]: 
				if r.password == request.form["pass"]:
					session["username"] = r.username
					userName = r.username
					if(userName not in users):
						users[userName] = r.password
					return redirect(url_for("homepage", username=r.username)) 
				else: 
					flash("Invalid Password, please try again!")
					#return redirect to ensure post requests not made in succession
					return redirect(url_for("login"))
					
		#check if any results from query
		if len(request.form["user"]) == 0:
			#if here, no username was entered
			flash("You must enter a username!")
		else:
			#if here, no matching usernames were found
			flash("Invalid username, please try again!")
		
		#return redirect to ensure post requests not made in succession
		return redirect(url_for("login"))
	
		
	return render_template("login.html")

@app.route("/homepage/<username>", methods=["GET", "POST"])
def homepage(username=None):
    if not username:
        return redirect(url_for("login"))
    else:
        if request.method == "POST":
            if not request.form.get("recipe"):
                favorited_recipe = request.form["favorite_recipe"]
                return redirect(url_for("homepage_favorite", favorited_recipe = favorited_recipe))
            val = request.form["recipe"] 
            return redirect(url_for("recipes", value = val))
        else:
            favorited_recipes = []
            user = User.query.all()
            favorited_recipe = User_Favorited_Recipes.query.all()
            for x in user:
                if x.username == session["username"]:
                    user_id = x.id
                    for y in favorited_recipe:
                        if y.user_id == user_id:
                            favorited_recipes.append(y.recipe_title)
                    return render_template("homepage.html", favorited_recipes = favorited_recipes)
            return render_template("homepage.html")

@app.route("/homepage/liked_recipe/<favorited_recipe>", methods=["GET", "POST"])
def homepage_favorite(favorited_recipe=None):
    r = showRecipe(favorited_recipe)
    return render_template("homepage_liked_recipe.html", favorited_recipe = r)

@app.route("/recipe/<value>", methods =["GET", "POST"])
def recipes(value=None):
    if not value:
        return render_template("homepage.html", username = session["username"])
    else:
        if request.method == "POST":
            recipe_name = request.form["viewRecipe"] 
            return redirect(url_for("recipe_name", recipe = recipe_name))
        recipe_list.clear()
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

@app.route("/recipe_name/liked_recipe/<recipe_name>", methods =["GET", "POST"])
def like_recipe(recipe_name=None):
    recipe_list = showRecipe(recipe_name)
    recipe_name = recipe_list[1]
    recipe_ingredients = recipe_list[3]
    recipe_instructions = recipe_list[5]
    liked_recipe = User_Favorited_Recipes(recipe_name, recipe_ingredients, recipe_instructions)
    db.session.add(liked_recipe)
    db.session.commit()
    result = User.query.all()
    for r in result:
        if r.username == session["username"]:
            user_id = r.id
            liked_recipe.user_id = user_id
            db.session.commit()
    return render_template("liked_recipe.html", recipe_name = recipe_name)


#routing for register page
@app.route('/registration/', methods=['GET', 'POST'])
def registration():
	"""Registers the user."""

	if request.method == 'POST':
		if not request.form['username']: #no username entered
			flash('You have to enter a username')
		elif len(request.form['username']) > 20: #make sure username is within valid character count
			flash('Your username has to be less than 20 characters!')
		elif any(letter in request.form['username'] for letter in special_chars): #checks for special characters
			flash('Your username contains invalid special characters!')
		elif not request.form['password']: #no password entered
			flash('You have to enter a password')
		elif len(request.form['password']) > 20: #make sure password is within valid character count
			flash('Your password has to be less than 20 characters!')
		elif any(letter in request.form['password'] for letter in " "): #checks for spaces
			flash('Your password contains space(s)!')
		elif request.form['password'] != request.form['password2']: #passwords do not match
			flash('The two passwords do not match')
		elif get_user_id(request.form['username']) is not None: #username already exists
			flash('The username is already taken')
		else:
			#add the new user to the db
			db.session.add(User(request.form['username'], request.form['password'])) #add new user to db
			db.session.commit() #commit new user to db
			flash('You were successfully registered and can login now') #confirm user successfully registered
			return redirect(url_for('login'))
			
		#return redirect to ensure post requests not made in succession
		return redirect(url_for("registration"))
			
	return render_template("registration.html")
	
#helper method from example code to check if username already exists
def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None
	
@app.route("/logout/")
def logout():
	if "username" in session:
		session.clear()
		flash('You have been logged out!')
		return redirect(url_for("login"))
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
    recipe_ing_fixed = []
    for key, value in data.items():
        if recipe.lower() in value['title'].lower():
            recipe_name_list.append("Recipe Name")
            recipe_name_list.append(value['title'])
            recipe_name_list.append("Ingredients")
            recipe_ingredients = value['ingredients']
            for x in recipe_ingredients:
                recipe_ing_fixed.append(x)
                recipe_ing_fixed.append(' ')
            ing_string = ''.join(recipe_ing_fixed)
            recipe_name_list.append(ing_string)
            recipe_name_list.append("Instructions")
            recipe_name_list.append(value['instructions'])
    return recipe_name_list

app.secret_key = "asdf;lkj"
            
if __name__ == "__main__":
    app.run()





