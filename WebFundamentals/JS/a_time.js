  var prompt = require('prompt');

  var properties = [
    {
      name: 'HOUR',
      validator: /^(0?[1-9]|1[01])$/,
      warning: 'Input cannot be Empty or Hour should be only number and between 0-11'
    },
    {
      name: 'MINUTE',
      validator: /^[0-5][0-9]$/,
      warning: 'Input cannot be Empty or Minute should be only number and between 0-59'
    },
    {
      name: 'PERIOD',
      validator: /^[AM]|[PM]$/,
    }
  ];

  prompt.start();

  prompt.get(properties, function (err, result) {
    if (err) { return onErr(err); }


    console.log('Time Input- ' + result.HOUR + ':' + result.MINUTE + ' ' + result.PERIOD);

    console.log('Assignment Output')
    if (result.HOUR.length == 0 && result.MINUTE.length ==  0 && result.PERIOD.length == 0){
                console.log ('Please input some values')
    }
    else if (result.HOUR.length == 0){
                console.log ('Hour cannot be empty')
    }
    else if (result.MINUTE.length ==  0){
                console.log ('Minute cannot be empty')
    }
    else if (result.PERIOD.length == 0){
                console.log ('Period cannot be empty')
    }

    else if (result.HOUR == 11 && result.MINUTE >= 30 && result.PERIOD == 'AM'){
		 var hr = 1 + parseInt(result.HOUR);
                console.log ('Its almost '+ hr + ' ' + ' Noon')
    }
    else if (result.HOUR == 11 && result.MINUTE >= 30 && result.PERIOD == 'PM'){
                 var hr = 1 + parseInt(result.HOUR);
                console.log ('Its almost '+ hr + ' ' + ' Mid Night')
    }
    else if (result.MINUTE >= 30 && result.PERIOD == 'AM'){
		var hr = 1 + parseInt(result.HOUR);
                console.log ('Its almost '+ hr + ' ' +result.PERIOD + ' in the morning')
    }
    else if
        (result.MINUTE >= 30 && result.PERIOD == 'PM'){
		hr= 1 + parseInt(result.HOUR);
                console.log ('Its almost ' + hr + ' ' + result.PERIOD + ' in the evening')
    }
    else if
        (result.MINUTE <= 29 && result.PERIOD == 'AM'){
                console.log ('Its just after ' + result.HOUR + ' ' + ' ' + result.PERIOD + ' in the morning')
    }
    else
                console.log ('Its just after ' + result.HOUR + ' ' + ' ' + result.PERIOD + ' in the evening')
  });

  function onErr(err) {
    console.log(err);
    return 1;
  }
