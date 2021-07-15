from flask_sqlalchemy import SQLAlchemy
#models
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(80), unique = True)
    password = db.Column(db.String(20))

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
            return '<User %r>' % self.username

class User_Favorited_Recipes(db.Model):
    __tablename__ = 'user_favorited_recipes'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    recipe_title = db.Column(db.String(40))
    recipe_ingredients = db.Column(db.String(2000))
    recipe_instructions = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, recipe_title, recipe_ingredients, recipe_instructions):
        self.recipe_title = recipe_title
        self.recipe_ingredients = recipe_ingredients
        self.recipe_instructions = recipe_instructions

    def __repr__(self):
            return '<User Favorited Recipe %r>' % self.recipe_title

