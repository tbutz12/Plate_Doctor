import json
from bs4 import BeautifulSoup
import grequests
import threading, queue
import random

q = queue.Queue()

def populateLinks():
    links = [
    "https://www.simplyrecipes.com/breakfast-recipes-5091541"
    "https://www.simplyrecipes.com/lunch-recipes-5091263",
    "https://www.simplyrecipes.com/dinner-recipes-5091433",
    "https://www.simplyrecipes.com/dessert-recipes-5091513",
    "https://www.simplyrecipes.com/drink-recipes-5091323",
    "https://www.simplyrecipes.com/snacks-and-appetizer-recipes-5090762",
    "https://www.simplyrecipes.com/holiday-and-seasonal-recipes-5091321",
    "https://www.simplyrecipes.com/quick-dinner-recipes-5091422",
    "https://www.simplyrecipes.com/easy-healthy-recipes-5091254",
    "https://www.simplyrecipes.com/quick-vegetarian-recipes-5091240",
    "https://www.simplyrecipes.com/easy-pasta-recipes-5090997",
    "https://www.simplyrecipes.com/easy-chicken-recipes-5091132",
    "https://www.simplyrecipes.com/all-the-burger-recipes-youll-need-for-your-next-cookout-5189791",
    "https://www.simplyrecipes.com/12-grilling-recipes-for-memorial-day-5179936",
    "https://www.simplyrecipes.com/recipes-by-diet-5091259",
    "https://www.simplyrecipes.com/recipes-by-method-5091235",
    "https://www.simplyrecipes.com/recipes-by-ingredients-5091192",
    "https://www.simplyrecipes.com/recipes-by-time-and-ease-5090817",
    "https://www.simplyrecipes.com/world-cuisine-recipes-5090811",
    "https://www.simplyrecipes.com/recipes/"
    ]
    return links

def getData(q):
    links = populateLinks()
    reqs1 = (grequests.get(l) for l in links)
    resp1 = grequests.map(reqs1)
    urls = []
    try:
        for r in resp1:
            soup = BeautifulSoup(r.content, "html.parser")
            links = soup.find_all('a')
            for x in links:
                urls.append(x.get('href'))
    except Exception:
        pass
    reqs2 = (grequests.get(u) for u in urls)
    resp2 = grequests.map(reqs2)
    l = {}
    for r in resp2:
        dic = {}
        try:
            ingredients = []
            instructions = []
            soup = BeautifulSoup(r.content, "html.parser")
            results_title = soup.find(id="recipe-block_1-0")
            for title in results_title.find_all("h2", class_="comp recipe-block__header text-block"):
                dic['title'] = str(title.get_text()).strip()
            result_ingredients = soup.find(id="ingredient-list_1-0")
            for ing in result_ingredients.find_all("li", class_="simple-list__item js-checkbox-trigger ingredient text-passage"):
                ingredients.append(str(ing.get_text()).strip("\n"))
            dic['ingredients'] = ingredients
            result_instruction = soup.find(id="structured-project__steps_1-0")
            for instr in result_instruction.find_all("li", class_="comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup"):
                if instr.find(class_='comp mntl-sc-block mntl-sc-block-html'):
                    ins = instr.find(class_='comp mntl-sc-block mntl-sc-block-html').get_text()
                    ins = str(ins)
                    ins.strip("\n")
                    instructions.append(ins)
            dic['instructions'] = instructions
            result_picture = soup.find(id="figure_2-0")
            for pic in result_picture("div", class_="img-placeholder"):
                picture_full = pic.find("img")
                picture = picture_full["src"]
                dic['picture'] = str(picture)
            l[str(random.randint(2,100000000))] = dic
        except Exception:
            pass
    q.put(l)

def startThread():
    thr1 = threading.Thread(target=getData, args=(q,), kwargs={})
    thr1.start()
    dumpJSON()

def dumpJSON():
    data = q.get()
    with open('data.json', 'w') as outfile:
         json.dump(data, outfile)

if __name__ == "__main__":
    startThread()