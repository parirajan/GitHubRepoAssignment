var penny = 0.01;

for (var i=2; i<=1032; i++){
	penny += penny;
	console.log('The reward on day - ', i ,'is $',penny);
	if (penny > 10000 && penny < 11000){
	console.log('Servant made $10,000 on ', i, 'days') 
	}
        if (penny > 1000000000 && penny < 2000000000){
        console.log('Servant made $1,000,000,000 on ', i, 'days')
        }
        if (penny > 1.1505236063118822e+308){
        console.log('Javascript reached infinity on ', i, 'loops')
        }
}
