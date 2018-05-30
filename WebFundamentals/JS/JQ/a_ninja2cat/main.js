$('document').ready(function() { //when the page is loaded...

    $('img').click(function() { //if an img is clicked on
        var alt = $(this).attr('alt-pic'), //set alt to the alt-pic attribute of that image
            src = $(this).attr('src'); //set src to the src attribute of that image
        $(this).attr('src', alt); //swap src with alt
        $(this).attr('alt-pic', src); //swap alt with src
    }); //click function
    
}); //page load function
