var numbersOnly = function(items) {
  var tempHolder = [];

  for (var i = 0; i<=items.length; i++){
    if (typeof items[i] == "number"){
      tempHolder.push(items[i]);
      }
    }
  return tempHolder;
}
var inputArray = numbersOnly([1, "apple", -3, "orange", 0.5]);
console.log(inputArray);
