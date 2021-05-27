var json = require('recipes.json'); //(with path)
var json2 = JSON.stringify(json);
console.log(json2);

var fs = require('fs');
fs.writeFile('recipes.json', json, 'utf8', callback);