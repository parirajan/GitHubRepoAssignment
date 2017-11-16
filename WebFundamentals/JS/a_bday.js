var daysUntilMyBirthday = 60;

for (var i = 60; i >= 0; i--){
	if (i <= daysUntilMyBirthday && i >= 31){
		console.log((i) + 'days until my birthday. Such a long time...;');
		}
	else if (i <= daysUntilMyBirthday && i <=31 && i >= 6){
 		console.log((i) + 'days until my birthday. I am excited...;');
		}
        else if (i <= daysUntilMyBirthday && i <=5 && i >= 1){
                console.log((i) + 'days until my birthday.');
                }
	else {
		console.log('Happy Birthday!!!')
		}
}

