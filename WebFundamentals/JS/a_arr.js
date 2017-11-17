function printArray(symbol){
var arr = ["James", "Jill", "Jane", "Jack"];
    console.log('The Array is -', arr);
    console.log(
        '\n0', symbol + arr[0],
        '\n1', symbol + arr[1],
        '\n2', symbol + arr[2],
        '\n3', symbol + arr[3]);
}


var prompt = require('prompt');


var properties = [
  {
    name: 'symbol',
    validator: /^[=]|[=>]|[::]|[-----]$/,
    warning: 'Input Symbol can only contain -  (ex: "->", "=>", "::", "-----")'
  }
];

prompt.start();

  prompt.get(properties, function (err, result) {
    if (err) { return onErr(err); }
    console.log('Command-line input received:');
    printArray(result.symbol);
  });

  function onErr(err) {
    console.log(err);
    return 1;
  }
