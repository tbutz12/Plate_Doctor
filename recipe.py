import json

with open("recipes_raw_nosource_epi.json") as f:
    data = json.load(f)
    
val = input("Enter a recipe to search for: ")
for key, value in data.items():
    if val.lower() in value['title'].lower():
        print(value['title'])





