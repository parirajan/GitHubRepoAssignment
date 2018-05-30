$(document).ready(function() {

	$('img').hover(function() { //hover function
		var src = $(this).attr('src'), //sets src as a local var
			alt = $(this).attr('alt-pic'); //same for alt-pic
		$(this).attr('src', alt); //swaps src with alt
		$(this).attr('alt-pic', src); //swaps alt with src
	}, function() { //does the same thing (works as a swap) for hover out
		var src = $(this).attr('src'),
			alt = $(this).attr('alt-pic');
		$(this).attr('src', alt);
		$(this).attr('alt-pic', src);
	});

});
