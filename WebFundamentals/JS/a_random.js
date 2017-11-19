function randomChance(InputQuarters,LeaveNow){
    if(LeaveNow === null || LeaveNow === undefined || LeaveNow === ''){
	console.log("Player wants to play till looses all InputQuarters");
	while(InputQuarters>0){
	//Determine if the player wins!
	InputQuarters -=1;
	//Determine 1 in 100 chance of winning
	var win = Math.floor(Math.random() * 101);
	if (win == 100){
	    //Determine the total winner amount between 50 and 100 InputQuarters
	    var winner = win = Math.floor(Math.random() * 100) + 50;
       	    console.log("You won with [" + InputQuarters + "] left. Your winnings are: [" + winner + "] InputQuarters");
	    return InputQuarters + winner;
	}
	}
	console.log("You lost with [" + InputQuarters + "] left.");
	return 0;
	}
	else {
        console.log("Player wants to LeaveNow after winning" + LeaveNow +"InputQuarters");
        while(InputQuarters<LeaveNow && InputQuarters > 0){
        //Determine if the player wins!
        InputQuarters -=1;
        //Determine 1 in 100 chance of winning
        var win = Math.floor(Math.random() * 101);
        if (win == 100){
            //Determine the total winner amount between 50 and 100 InputQuarters
            var winner = win = Math.floor(Math.random() * 100) + 50;
            console.log("You won with [" + InputQuarters + "] left. Your winnings are: [" + winner + "] InputQuarters");
	    InputQuarters += winner;
        }
	if(InputQuarters >= LeaveNow){
            return InputQuarters;
        }
        }
        console.log("You lost with [" + InputQuarters + "] left.");
        return 0;
	}
	}


//console.log(randomChance(100,500));


var prompt = require('prompt');


var properties = [
  {
    name: 'InputQuarters',
    validator: /^[0-9]|[0-9]|[0-9]$/,
    warning: 'Input Quarters can only be numbers and should not be negative'
  },
  {
    name: 'LeaveNow',
    validator: /^[0-9]|[0-9]|[0-9]$/,
    warning: 'Input Quarters can only be numbers and should not be negative'
  }
];

prompt.start();

  prompt.get(properties, function (err, result) {
    if (err) { return onErr(err); }
    console.log('Command-line input received:');
    randomChance(result.InputQuarters,result.LeaveNow);
  });

  function onErr(err) {
    console.log(err);
    return 1;
  }

