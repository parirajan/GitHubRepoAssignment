$(document).ready(function() {
	var $mainh2 = $('#mainCard h2'), //#mainCard h2 tag...won't work after .html() is applied
		$mainBtn = $('#mainCard button'), //mainCard button...same
		$mainP = $('#mainCard p:nth-child(3)'), //mainCard p tag...same
		counter = 0, //starts timer at 0
		baconHTML =
		"<h2 id='baconH'>BACON!!!</h2><img id='bacon' src='http://big.assets.huffingtonpost.com/slide_297900_2459978_free.gif' alt='Sizzling Bacon' />",
		isHungryHTML =
		"<main><article id='mainCard'><h2>Is Anyone Else Hungry?</h2><form><label for='hungryY'>Yes&nbsp;</label><input type='radio' name='hungry' id='hungryY' value='hungry' /><label for='hungryN'>No&nbsp;</label><input type='radio' name='hungry' id='hungryN' value='notHungry' /></form><button>Next</button><p id='firstP'></p><p id='secondP'></p></article></main>",
		lastHTML =
		"<main><article id='notHungryCard'><h2>You're Here Because Apparently You're Not Hungry and Don't Like Bacon So I Can Only Assume That You Don't Have a Soul...</h2><button>Next</button><p>Hah, nah, I'm just kidding!</p><p>Click next to move on.</p></article><article id='hungryCard'><h2>Well, That Was Fun</h2><p>You've seen a lot of what JQuery can do, reference the list below of methods you've played with (hover over an item to get a description):</p><ul><li id='addClass'><span>.addClass()</span></li><li id='after'><span>.after()</span></li><li id='append'><span>.append()</span></li><li id='attr'><span>.attr()</span></li><li id='before'><span>.before()</span></li><li id='click'><span>.click()</span></li><li id='data'><span>.data()</span></li><li id='fadeIn'><span>.fadeIn()</span></li><li id='fadeOut'><span>.fadeOut()</span></li><li id='focus'><span>.focus()</span></li><li id='hide'><span>.hide()</span></li><li id='show'><span>.show()</span></li><li id='slideDown'><span>.slideDown()</span></li><li id='slideToggle'><span>.slideToggle()</span></li><li id='slideUp'><span>.slideUp()</span></li><li id='text'><span>.text()</span></li><li id='toggle'><span>.toggle()</span></li><li id='val'><span>.val()</span></li></ul><p>Now get out there and see what you can come up with...or click the button below to see this again.</p><p>And go get some bacon/tofurkey, whatever tickles your fancy!</p><button>Start Again</button></article></main>";

	$('#mainCard').hide(); //hide mainCard for now

	$('body').data('info', { //data object for last slide
		addClass: 'Adds the specified class(es) to each element in the set of matched elements.',
		after: 'Insert content, specified by the parameter, after each element in the set of matched elements.',
		append: 'Insert content, specified by the parameter, to the end of each element in the set of matched elements.',
		attr: 'Get the value of an attribute for the first element in the set of matched elements or set one or more attributes for every matched element.',
		before: 'Insert content, specified by the parameter, before each element in the set of matched elements.',
		click: 'Bind an event handler to the "click" JavaScript event, or trigger that event on an element.',
		data: 'Store arbitrary data associated with the matched elements or return the value at the named data store for the first element in the set of matched elements.',
		fadeIn: 'Display the matched elements by fading them to opaque.',
		fadeOut: 'Hide the matched elements by fading them to transparent.',
		focus: 'Bind an event handler to the “focus” JavaScript event, or trigger that event on an element.',
		hide: 'Hide the matched elements.',
		show: 'Display the matched elements.',
		slideDown: 'Display the matched elements with a sliding motion.',
		slideToggle: 'Display or hide the matched elements with a sliding motion.',
		slideUp: 'Hide the matched elements with a sliding motion.',
		text: 'Get the combined text contents of each element in the set of matched elements, including their descendants, or set the text contents of the matched elements.',
		toggle: 'Display or hide the matched elements./Bind two or more handlers to the matched elements, to be executed on alternate clicks.',
		val: 'Get the current value of the first element in the set of matched elements or set the value of every matched element.'
	}); //.data

	function liHover(item) { //function for when an li is hovered over
		switch (item) { //add a p tag based on the item overed over
			case 'addClass':
				$('#addClass').append("<p class='endList'>" + $('body').data('info').addClass +
					"</p>");
				break;
			case 'after':
				$('#after').append("<p class='endList'>" + $('body').data('info').after +
					"</p>");
				break;
			case 'append':
				$('#append').append("<p class='endList'>" + $('body').data('info').append +
					"</p>");
				break;
			case 'attr':
				$('#attr').append("<p class='endList'>" + $('body').data('info').attr +
					"</p>");
				break;
			case 'before':
				$('#before').append("<p class='endList'>" + $('body').data('info').before +
					"</p>");
				break;
			case 'click':
				$('#click').append("<p class='endList'>" + $('body').data('info').click +
					"</p>");
				break;
			case 'data':
				$('#data').append("<p class='endList'>" + $('body').data('info').data +
					"</p>");
				break;
			case 'fadeIn':
				$('#fadeIn').append("<p class='endList'>" + $('body').data('info').fadeIn +
					"</p>");
				break;
			case 'fadeOut':
				$('#fadeOut').append("<p class='endList'>" + $('body').data('info').fadeOut +
					"</p>");
				break;
			case 'focus':
				$('#focus').append("<p class='endList'>" + $('body').data('info').focus +
					"</p>");
				break;
			case 'hide':
				$('#hide').append("<p class='endList'>" + $('body').data('info').hide +
					"</p>");
				break;
			case 'show':
				$('#show').append("<p class='endList'>" + $('body').data('info').show +
					"</p>");
				break;
			case 'slideDown':
				$('#slideDown').append("<p class='endList'>" + $('body').data('info').slideDown +
					"</p>");
				break;
			case 'slideToggle':
				$('#slideToggle').append("<p class='endList'>" + $('body').data('info').slideToggle +
					"</p>");
				break;
			case 'slideUp':
				$('#slideUp').append("<p class='endList'>" + $('body').data('info').slideUp +
					"</p>");
				break;
			case 'text':
				$('#text').append("<p class='endList'>" + $('body').data('info').text +
					"</p>");
				break;
			case 'toggle':
				$('#toggle').append("<p class='endList'>" + $('body').data('info').toggle +
					"</p>");
				break;
			case 'val':
				$('#val').append("<p class='endList'>" + $('body').data('info').val +
					"</p>");
				break;
		} //switch
	} //liHover

	/*********once timer is up for bacon...********/
	function timer() {
		$('body').html(isHungryHTML); //change body to isHungryHTML
		$('#styles').attr('href', 'defaultStyles.css'); //apply default styling
		$('button').css({ //buttons now need to have a top margin of 50px
			'margin-top': '50px'
		});
		$('#hungryN').focus(function() { //if the not hungry radio button is focused on...
			if ($('span').text()) { //is there already a span tag?
				$('span').text('Are you trippin?');
			} else { //if not, add one after the radio buttons
				$('form').after('<span>Are you trippin?</span>');
			} //hungryN if/else
		}); //hungryN.focus
		$('#hungryY').focus(function() { //if the hungry radio button is focused on...
			if ($('span').text()) { //is there already a span tag?
				$('span').text('Yessssss, Me too!!');
			} else { //if not, add one before the button (see what I did there??)
				$('button').before('<span>Yessssss, Me too!!</span>');
			} //hungryY if/else
		}); //hungryY.focus
		$('input').click(function() { //if one of the radio buttons is clicked...
			value = $('input:radio[name=hungry]:checked').val(); //store the value of that radio button in value
			if (value == 'hungry') { //if value is hungry......
				$('#firstP').text('MmmmMmMMmMmm Bacon.  Time for lunch!'); //change the text of the first p tag
				$('#secondP').text('Click the next button to proceed'); //change the text of the second p tag
				$('button').click(function() { //if the button is clicked...and value is hungry
					$('body').html(lastHTML); //change body HTML to the last slide
					$('#notHungryCard').toggle(); //toggle the notHungryCard to off
					$('button').css({ //button margin again!
						'margin-top': '50px'
					});
					$('button').click(function() { //if the start again button is clicked..
						location.reload(); //reload the page to start at the beginning
					});
					$('span').hover(function() { //if one of the li (spans!) is hovered over (makes it less cumbersome)
						idAttr = $(this).parent().attr('id'); //defines the id of the parent li element hovered over
						liHover(idAttr); //run the liHover function with the given id
					}, function() { //when the mouse is no longer hovered over that given span
						$('.endList').remove(); //remove the appended p tag
					}); //span.hover
				}); //hungry button.click
			} else { //if value is NOT hungry!
				$('#firstP').text('Really??????'); //change the text of the first p tag
				$('#secondP').text('Click the next button to proceed'); //change the text of the second p tag
				$('button').click(function() { //if you are not hungry and you click on the button...
					$('body').html(lastHTML); //load the last page HTML
					$('#styles').attr('href', 'baconStyles.css'); //apply baconStyles
					$('#hungryCard, button, p').toggle(); //toggle the last slide, button, and p tag to be hidden
					window.setTimeout(function() { //after 2 seconds...
						$('button, p').slideDown(); //apply the slideDown method to the button and p tags
					}, 2000);
					$('button').css({ //top margin 50px for the button!
						'margin-top': '50px'
					});
					$('button').click(function() { //upon clicking the button...
						$('#styles').attr('href', 'defaultStyles.css'); //apply defaultStyles again
						$('#hungryCard, #notHungryCard').slideToggle(); //slideToggle the notHungryCard to the last slide
						$('button').click(function() { //if the start again button is clicked...
							location.reload(); //reload the page to start over
						});
						$('span').hover(function() { //if one of the li span elements is hovered over...
							idAttr = $(this).parent().attr('id'); //define idAttr as the parent's id
							liHover(idAttr); //call the liHover function
						}, function() { //when no longer hovered over...
							$('.endList').remove(); //remove the appended p tag
						}); //.hover
					}); //hell button.click
				}); //not hungry button.click
			} //hungry/not hungry if/else
		}); //radio button.click
	} //timer function

	/********Moves to the 2nd slide********/
	$('#start').click(function() {
		$('#introCard').slideUp(); //introCard is gone now
		$('#mainCard').show(); //mainCard is now in use!
	});

	/********Moves on from there...********/
	$mainBtn.click(function() {
		if (counter === 0) { //if it's the first time the next button has been clicked...(slide2)
			$mainh2.fadeOut('slow'); //fadeOut the header tag
			$mainP.addClass('redify'); //make the main P tag background red and white text
			$mainh2.text('Get Ready!'); //change the header text
			$mainP.text('Add .addClass and .text to the list!  Wooooooo!!'); //change the main P tag text
			$mainh2.fadeIn('slow'); //fadeIn the header tag
		} else if (counter == 1) { //if it's the second time the next button has been clicked...(slide3)
			$mainP.removeClass('redify'); //turn the main P tag back to normal
			$mainh2.text('HERE IT COMES!'); //change the header text
			$mainP.text(
				"Alright, enough of the child's play, let's do something awesome..."); //change the main P tag text
		} else if (counter == 2) { //if it's the third time the next button has been clicked...(slide4)
			$('body').html(baconHTML); //replace the body HTML with baconHTML
			$('#styles').attr('href', 'baconStyles.css'); //apply baconStyles
			window.setTimeout(timer, 3000); //execute the timer function after 3 seconds
		}
		counter++; //every time the main button is clicked, add 1 to counter
	}); //mainBtn.click
}); //page load function
