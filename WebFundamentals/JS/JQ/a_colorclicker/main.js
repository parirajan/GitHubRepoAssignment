function random_color()
{
   var rgb = ['a','b','c','d','e','f','0','1','2','3','4','5','6','7','8','9'];
   color = '#';  //this is what we'll return!
   for(var i = 0; i < 6; i++)
   {
	  x = Math.floor((Math.random()*16));
	  color += rgb[x];
   }
   return color;
}

$(document).ready(function(){
   $('#large_box').click(function(){
     random_color(); //runs random_color to generate a hex color
     $(this).css('background-color', color); //changes the background color of the large box
     $(this).children().css('background-color', color); //changes the background color of the smaller boxes
     event.stopPropagation(); //stops the Propagation!
	  // alert('you clicked the big box!');
//comment this out when you have figured out what event.stopPropagation is used for
   });

   $('.side_box').click(function(event){
     random_color(); //runs random_color
     $(this).siblings().css('background-color', color); //changes the background color of the siblings
     event.stopPropagation(); //stops the Propagation!
  });

   $('.middle_box').click(function(event){
     random_color(); //runs random_color
     $(this).parent().css('background-color', color); //changes the background color of the large box
     event.stopPropagation(); //stops the Propagation!
  });
});
