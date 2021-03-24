![Spiraloid-Toolkit-for-Blender-3DComicToolkit](https://github.com/spiraloid/Spiraloid-Toolkit-for-Blender-3DComicToolkit/blob/master/Resources/Reader/images/covers.jpg)

This is a 3D Comic toolkit for Blender that allows you to save out your own scrolling 3D Comic websites like https://3dcomic.shop .  I make it for myself to create my own 3D Comics and decided to share it.  I update it frequently as I use it to create my own titles so be warned.   I'm not really supporting this like a normal addon.  These are my personal custom 3D pencil customizations and sharpenings for Blender.  Since I get blender free.  I'm passing it on.   

The Toolkit comes with all you need to start creating your own 3D Comic directly from your Blender scenes.  These are not 2D rendered comics, but true 3D Comics where every panel is rendered live using real time 3D Graphics.  

Features:

-3D Panel scene manager.  Since every panel in your comic is a scene inside your .blend file, the scene manager will let you read and edit your comic directly inside Blender.   Adjusting all Lettering, Lighting, Visuals and story flow in context, just as you'd expect.

-Automatic 3D Comic Site Generator.   The workhorse of the toolkit.  It automatically combines, decimates, converts and exports a custom .glb file for every scene.  In one click, it automatically generates the entire 3D Comic website and opens a web browser with a local server so you can read it just your own 3D Comic following will.  To make it public, you just need upload the directory to your website.  (I use Github Pages to host 3dcomic.shop)

-Inkshade - This part of the Toolkit allows you to instantly create black and white "ink shaded" comic look from your 3D Scene in Eevee using a combination of custom nodes and modifiers.  The same look gets rebuilt automatically in the exported 3D Comic that will run in browsers.  (You will need to setup your own web hosting. I use github to serve 3Dcomic.shop)  

-Collection Baker.  Tool for combining, decimating, unwrapping, light baking your panel scenes in one click.  Essential for combining the best of cycles with real time 3D. 

-Inkbots! The Toolkit comes with a random assortment of 3D inkbot characters, wordballoons, captions and SFX to help get you started. Everything all set to be refined in edit mode.

-Pose Cycler - quickly cycle through character poses with the mouse wheel

-Multilingual Lettering.   Comics have a global audience so localizing your lettering works right out of the box, assuming you speak the language (or can use google translate).  Just set the active language and start adding in localized letters for that language.  The letters will be automatically exported and the 3D Comic site will know how to switch between them based on the letter URL.  For example, here's the Inkbots comic in spanish!

https://3dcomic.shop/inkbots/s01e01/index.html?lan=es

REQUIREMENTS:

a WINDOWS 10 PC (sorry I don't have a mac).

Blender 2.92 or later.
https://www.blender.org/download/releases/2-92/

Python 3.8 or later. 
(ALERT: be sure to check the box to add python to your environment path vairable on install.  this step is needed to make "read 3d comic" menu work since it runs a local python server)
https://www.python.org/ftp/python/3.8.5/python-3.8.5.exe

This repo is for live updates as I make fixes or improvements, you can also find the official release on gumroad at:
https://gumroad.com/l/3dcomictoolkit

Be warned, This is a tool I use and update frequently so there may be bugs and I may not care to fix them.   

INSTALLATION:  
click the green button and download the zip.   do not unpack just install the zipped addon as you would normally, be sure to deactivate and remove any previous versions.   
note: do not rename the zip or the addon folder that gets installed in your in addons directory. The load resources commands are hardcoded to assume the addon folder is named "Spiraloid-Toolkit-for-Blender-3DComicToolkit-master"

I'll try not to break things, but if you get stuck feel free to dig into the code yourseld orreport the issue here, and I'll see what I can do as I find the time  (it's free afterall).  

You may also find good tips and tricks by connecting with others interested who are also making 3D Comics in these Communities:
https://www.facebook.com/groups/3dcomic/
https://www.reddit.com/r/3DComic/

You can follow me on social media here:
https://linktr.ee/spiraloid

btw, If you make anything cool with this, send me a link!
The world needs more 3D Comics.  

-bay

ps: if you want to support 3d-comics, buy a t-shirt and go pro!

https://gumroad.com/l/3dcomictoolkit
https://www.amazon.com/dp/B08J2455QL

(you can sell your own shirts by apllying for a merch.amazon.com account)

