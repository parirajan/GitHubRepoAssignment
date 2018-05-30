$('document').ready(function() { //when document is loaded

	$('img').click(function(){ //if a ninja is clicked
        $(this).css('opacity', '0'); //turn its opacity to 0, but keep it in the DOM (don't use display none)
    });

    $('button').click(function(){ //when the reset button is pushed...
        $('img:last-child').css('display', 'block'); //unhide the keep calm ninja
        $('img').css('opacity', '.2'); //make the rest of the ninjas transparent
        window.setTimeout(function() { //first timer set at 15 ms after the keep calm ninja is unhidden
            $('img:last-child').css({ //make the keep calm ninja appear and grow!
                'opacity': '1',
                'width': '500px',
                'height': 'auto',
                'top': '0',
                'left': '32%'
            });
            window.setTimeout(function() { //second timer set at 3secs when the grow animation is complete
                $('img').css({'opacity': '1', 'transition': '2s'}); //make the other ninjas opaque and all ninjas transition the same
                $('img:last-child').css('opacity', '0'); //make the keep calm ninja disappear
                window.setTimeout(function() { //reset transition time for ninjas
                    $('img').css('transition', '.3s');
                }, 5);
                window.setTimeout(function(){ //reset keep calm ninja css after disappeared
                    $('img:last-child').css({
                        'display': 'none',
                        'width': '0',
                        'height': '0',
                    	'top': '35%',
                    	'left': '38%',
                        'transition': '3s'
                    }); //innermost timer css reset
                }, 2000); //innermost timer
            }, 3000); //second timer
        }, 15); //first timer
    }); //button click function
}); //page load function
