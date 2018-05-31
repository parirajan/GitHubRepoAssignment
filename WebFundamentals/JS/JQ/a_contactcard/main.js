$(document).ready(function() {
	$('#first').focus();
	$('form').submit(function() {
		if ($('#first').val() === "" || $('#last').val() === "" || $('#desc').val() === "") {
			alert('Please fill in all fields, thanks!');
			$('#first').focus();
			return false;
		} else {
			var contactHTML = '<article class="card"><h2>' + $('#first').val() + "&nbsp;" + $('#last').val() + '</h2><p>Click for description!</p><p class="hidden">' + $('#desc').val() + '</p></article>';
			$('main').css({'width': '800px'});
			$('form').css({
				'display': 'inline-block',
				'margin': '0 100px 0 40px'
			});
			$('#contact').append(contactHTML);
			$('input, textarea').val('');
			$('#add').val('Add User');
			$('#first').focus();
			return false;
		}
	});
	$('div').on('click', '.card', function() {
		$(this).children().toggle();
	});
});
