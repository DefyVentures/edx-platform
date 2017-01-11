// blocks.fields.html5_sources

String.prototype.replaceAll = function(s1, s2) {
  return this.split(s1).join(s2)
}

//var _find = 'old-string'
//var _repl = 'new-string'

function findreplace(collection) {
  var cursor = collection.find({}, {_id: 0});
  while (cursor.hasNext()) {
    var obj = cursor.next();
    var objStr = JSON.stringify(obj);
    if (objStr.split(_find).length > 1) {
      var newObjStr = objStr.replaceAll(_find, _repl);
      collection.update(obj, JSON.parse(newObjStr));
    }
  }
}

findreplace(db.modulestore);
findreplace(db.modulestore.structures);

