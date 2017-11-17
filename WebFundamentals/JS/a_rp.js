function printRange(start,end,incr){
    if (end == null && incr == null){
	end = start
	start = 0;
	incr = 1;
	}
    else if (end !== null && incr == null){
	incr = 1;
	}
    for (var i = start; i < end; i = i+incr)
            console.log(i);
}
printRange(-10.5,2,.5);


