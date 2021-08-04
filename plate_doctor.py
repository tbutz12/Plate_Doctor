import json, urllib.parse
from flask import Flask, request, url_for, redirect, session, render_template, flash
from models import db, User, User_Favorited_Recipes

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
			if not request.form.get("recipe") and not request.form.get("ingredients"): #POST issued, but neither recipe name nor ingredients populated
				if not request.form.get("favorite_recipe"): #the user did not select a favorited recipe either - all fields blank
					flash("Please populate one or more fields!")
					user = User.query.filter_by(username=session["username"]).first() #grab user
					favorites = User_Favorited_Recipes.query.filter_by(user_id=user.id).all() #grab user favorites (if they exist)
					if favorites:
						favorited_recipes = []
						for y in favorites:
							favorited_recipes.append(y.recipe_title)
						return render_template("homepage.html", favorited_recipes = favorited_recipes)
					else:
						return render_template("homepage.html")
					#return render_template("homepage.html")
				favorited_recipe = request.form.get("favorite_recipe")
				return redirect(url_for("homepage_favorite", favorited_recipe = favorited_recipe))
			
			#grab recipe name input from form
			recipe_name = request.form["recipe"]
			#if user did not enter a name, use a temp value for the address bar
			if not recipe_name:
				recipe_name = "search"
			
			#grab ingredients input from form
			ingredients = request.form["ingredients"] #split ingredients by commas 
			#if user did not enter ingredients, use a temp value for the address bar
			if not ingredients:
				ingredients = "noIngred"
								
			return redirect(url_for("recipes", value = recipe_name, ingredients = ingredients))
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
    recipe_name = r[1]
    return render_template("homepage_liked_recipe.html", favorited_recipe = r, recipe_name = recipe_name)

@app.route("/recipe/<value>/<ingredients>", methods =["GET", "POST"])
def recipes(value=None, ingredients=None):

	#clear any temp values
	if value == "search":
		value = ""
	if ingredients == "noIngred":
		ingredients = ""
			
	if not value and not ingredients:
		return render_template("homepage.html", username = session["username"])
	else:
		if request.method == "POST":
			recipe_name = request.form["viewRecipe"] 
			return redirect(url_for("recipe_name", recipe = recipe_name))
		recipe_list.clear()
		#declare r here
		r = []
		#need to check if user searching by recipe name, ingredients, or both
		if value and ingredients: #both name and ingredients
			#search both
			r = findByBoth(value, ingredients)
		elif value: #only name
			r = findRecipeName(value)
		elif ingredients:
			r = findRecipeIngredients(ingredients)
		
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
	recipe_name = recipe_list[1].strip()
	recipe_ingredients = str(recipe_list[3])
	recipe_instructions = str(recipe_list[5])	
	
	user = User.query.filter_by(username=session["username"]).first() #grab user
	check_recipe = User_Favorited_Recipes.query.filter_by(recipe_title=recipe_name, user_id=user.id).first()
	if check_recipe:
		flash("You already have this as a favorite!")
		return redirect(url_for("homepage", username=session["username"]))
	
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
	
@app.route("/homepage/liked_recipe/un_like_recipe/<recipe_name>", methods =["GET", "POST"])
def un_like_recipe(recipe_name=None):
	#make sure the user is valid
	if session["username"] == None:
		flash('You must login!')
		return redirect(url_for('login'))
	#now know there is a valid user logged in, unfavorite their recipe of choice
	curr_user = User.query.filter_by(username=session["username"]).first()
	removed_recipe = User_Favorited_Recipes.query.filter_by(recipe_title=recipe_name, user_id=curr_user.id).all()
	#have the unliked recipe, remove from db
	for curr in removed_recipe:
		db.session.delete(curr)
	#commit changes
	db.session.commit()
	return render_template("un_like_recipe.html", removed_recipe = recipe_name)

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


def findRecipeName(val):
    with open("data.json") as f:
        data = json.loads(f.read())
    for key, value in data.items():
        if val.lower() in value['title'].lower():
            if value['title'] in recipe_list:
                continue
            recipe_list.append(value['title'])
    return recipe_list
	
def findRecipeIngredients(ingredients):
	data = []
	ingredient_array = ingredients.split(",")
	
	with open("data.json") as f:
		data = json.load(f)
	#using a bool to check if valid recipe so far
	valid = True
	#loop through every entry in the JSON file
	for key, value in data.items():
		#loop through every ingredient in the list
		for curr_search in ingredient_array:
			#check against every ingredient in current ingredient array
			#grab length of ingredient list
			num_ingredients = len(value['ingredients'])
			curr_count = 1
			for curr_check in value['ingredients']:
				#if an ingredient is not found in the current recipe examined, flag it as invalid and break
				if curr_search.lower().strip() not in curr_check.lower() and curr_count == num_ingredients:
					valid = False
					break
				elif curr_search.lower().strip() in curr_check.lower():
					break #ingredient found, break
				curr_count = curr_count + 1
					
		#check if ingredients list is empty
		if not value['ingredients']:
			valid = False
		#check this recipe is a valid result, if so, add it to the list
		if valid:
			recipe_list.append(value['title'])
		#reset valid var
		valid = True
	return recipe_list
	

def findByBoth(name, ingredients):
	ingredient_array = ingredients.split(",")
	#using a bool to check if ingredients match recipe
	valid = True
	with open("data.json") as f:
		data = json.loads(f.read())
	for key, value in data.items():
		if name.lower() in value['title'].lower(): #check if entered recipe name matches current recipe 
			if value['title'] in recipe_list:
				continue

			#check ingredients since name matches
			#loop through every ingredient in the list
			for curr_search in ingredient_array:
				#check against every ingredient in current ingredient array
				#grab length of ingredient list
				num_ingredients = len(value['ingredients'])
				curr_count = 1
				for curr_check in value['ingredients']:
					#if an ingredient is not found in the current recipe examined, flag it as invalid and break
					if curr_search.lower().strip() not in curr_check.lower() and curr_count == num_ingredients:
						valid = False
						break
					elif curr_search.lower().strip() in curr_check.lower():
						break #ingredient found, break
					curr_count = curr_count + 1
						
			#check if ingredients list is empty
			if not value['ingredients']:
				valid = False
			#check this recipe is a valid result, if so, add it to the list
			if valid:
				recipe_list.append(value['title'])
			#reset valid var
			valid = True
				
	return recipe_list
	


def showRecipe(recipe):
    with open("data.json") as f:
        data = json.loads(f.read())
    recipe_name_list = []
    recipe_ing_fixed = []
    recipe_instr_fixed = []
    for key, value in data.items():
        if recipe.lower() in value['title'].lower():
            if value['title'] in recipe_name_list:
                continue
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





