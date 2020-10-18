document.cookie = 'name=3dcomicshop; ; SameSite=Secure;'

if (document.getElementById) {
    window.onload = swap
};
function swap() {
    var el=document.getElementById("banner");	
    rndimg = new Array(
        "./images/cover_1.jpg",
        "./images/cover_2.jpg",
		"./images/cover_3.jpg",
		"./images/cover_4.jpg",
		"./images/cover_5.jpg",
		"./images/cover_6.jpg",
		"./images/cover_7.jpg",
		"./images/cover_8.jpg"
    );

	var numimages = rndimg.length;
	var imgObjects = [];
	for (var i=0;i < rndimg.length; i++) {
			imgObjects[i] = new Image();
			imgObjects[i].src = rndimg[i]; 
	}

	var x=(Math.floor(Math.random()*numimages));						
	randomimage=(imgObjects[x].src);
	el.src = randomimage ; 
}
