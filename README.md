![Spiraloid-Toolkit-for-Blender-3DComicToolkit](https://github.com/spiraloid/Spiraloid-Toolkit-for-Blender-3DComicToolkit/blob/master/Resources/Reader/images/covers.jpg)
 
[Getting Started Video](https://user-images.githubusercontent.com/36362743/112266687-97067100-8c31-11eb-881f-9e3f3c7d42c5.mp4)


This is a 3D Comic toolkit for Blender that allows you to save out your own scrolling 3D Comic websites like https://3dcomic.shop .  I make it for myself to create my own 3D Comics and decided to share it.  I update it frequently as I use it to create my own titles so be warned.   I'm not really supporting this like a normal addon.  These are my personal custom 3D pencil customizations and sharpenings for Blender.  Since I get blender free.  I'm passing it on.   

The Toolkit comes with all you need to start creating your own 3D Comic directly from your Blender scenes.  These are not 2D rendered comics, but true 3D Comics where every panel is rendered live using real time 3D Graphics.  

---

Features:

-3D Panel scene manager.  Since every panel in your comic is a scene inside your .blend file, the scene manager will let you read and edit your comic directly inside Blender.   Adjusting all Lettering, Lighting, Visuals and story flow in context, just as you'd expect.

-Automatic 3D Comic Site Generator.   The workhorse of the toolkit.  It automatically combines, decimates, converts and exports a custom .glb file for every scene.  In one click, it automatically generates the entire 3D Comic website and opens a web browser with a local server so you can read it just your own 3D Comic following will.  To make it public, you just need upload the directory to your website.  (I use Github Pages to host 3dcomic.shop)

-Inkshade - This part of the Toolkit allows you to instantly create black and white "ink shaded" comic look from your 3D Scene in Eevee using a combination of custom nodes and modifiers.  The same look gets rebuilt automatically in the exported 3D Comic that will run in browsers.  (You will need to setup your own web hosting. I use github to serve 3Dcomic.shop)  

-Collection Baker.  Tool for combining, decimating, unwrapping, light baking your panel scenes in one click.  Essential for combining the best of cycles with real time 3D. 

-Inkbots! The Toolkit comes with a random assortment of 3D inkbot characters, wordballoons, captions and SFX to help get you started. Everything all set to be refined in edit mode.

-Pose Cycler - quickly cycle through character poses with the mouse wheel

-Multilingual Lettering.   Comics have a global audience so localizing your lettering works right out of the box, assuming you speak the language (or can use google translate).  Just set the active language and start adding in localized letters for that language.  The letters will be automatically exported and the 3D Comic site will know how to switch between them based on the letter URL.  For example, here's the Inkbots comic in spanish!

https://3dcomic.shop/inkbots/s01e01/index.html?lan=es

---

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

---

INSTALLATION:  
click the green button and download the zip.   do not unpack just install the zipped addon as you would normally, be sure to deactivate and remove any previous versions.   
note: do not rename the zip or the addon folder that gets installed in your in addons directory. The load resources commands are hardcoded to assume the addon folder is named "Spiraloid-Toolkit-for-Blender-3DComicToolkit-master".  don't download duplicates and install as a file named Spiraloid-Toolkit-for-Blender-3DComicToolkit-master (1).zip will break.

I'll try not to break things, but if you get stuck feel free to dig into the code yourself, or report the issue here, and I'll see what I can do as I find the time  (it's free afterall).  

---

GETTING STARTED:

To make a 3D comic, you must have the .blend file and the folders where it's saved in exactly a very specific way.   Fortunately, the toolkit handles all of this for you (most of the time - but it's very easy for you to creak things should you stray from the golden path)  Because of this, I strongly recomend using blender copy-paste feature that lets you copy and paste 3D models between two running versions of blender. treat one version like a working scene where it's ok to be messy, and treat the other version with your Comic_v.001.blend as the golden version that you know will build correctly.  If you keep this file efficient and cleanly organized you shouldn't run into much trouble.  Here's how to make that file.

1: “3DComics > Create a new 3D comic”

This will create all the folders and save your 3D Comic a blend file in the correct location.

2: “3DComics > Panel > Insert a row” 

This will create a comic panel scene.  Typically each row only has 1 panel in it, but if you need to make a split panels, a choose larger number and the split scenes will get  arranged side by side on the same row.  (PROTIP: panel width and height dimensions are determined by the naming convention of each scene name ) 

2: Make your 3D Comic art.  remember what I wrote above about copy and paste.  use meshes and grease pencils strokes only.  I recommend making a black and white comics since it saves on texture memory.  Use  “3DComics > Color > Inkshade visible” to automatically create the ink outline modifiers for all the visible objects with a spotlight.  You will likely need to adjust the "WhiteOutline" modifiers thickness per object to get the line art feeling right.  depending on the scale, you might also want to adjust the "InkThickness" modifiers influence mask texture scale as wel l (in case it looks too "bumpy")

Once you have your ink looking right, you can use “3DComics > Utilities > Toggle Workmode” to turn them on and off while you work (they triple your scene polycount).  I have my  keyboard shorkey for this set to tab since I use it constantly, (which means use cntrl-tab, e and double click to toggle edit mode) 

3: Make sure evedrything you want to be in the 3D Comic panel into the collection named Export.##### in each panel scene.  Only objects in this collection will be exported.  All modifiers will be applied on export.  The panels themselves are rendered in browsers on lots of different devices so keep the output polycount if each panel scene under  100,000 triangles.  This polycount includes the scene, ink outlines, letters and grease pencil lines. So decimate aggressively.

5: To Add letters, use “3DComics > Letters > Add Wordballoon”  you can select, move remodel the balloons as you like in edit mode.  To change the text,  select it and enter edit mode to rewrite it.  (you also might want to pick out a good comic lettering font for your title from comicbookfonts.com or blambot.com)  The word balloons are parented to the camera and can be switched by setting the active language to reach more people.   The default is english. 

6: “3DComics > Build 3D Comic”
Assuming you installed everything correctly (and didn’t mess with the naming or leave weirdness in your scene collections by mistake) a web browser should open with your 3D comic!  
now make it better! 

7: “3DComics > Quick Export Panel”
This is how I like to test out the comic in chrome.  I usually spend a lot of time on just a single panel so this is a quick way to only export the current scene without having to wait for every scene to compile and export.  I use this so much have this set to ctrl+shift+e shortcut.  

(PROTIP:  In your web browser, the 3D comic should reload automatically, however this can fail sometimes.  if you browser isn't showing the latest awesomeness. make sure you're looking at the right tab and hold down the shift key when you press reload page button)

PUBLISHING:
Even though you are seeing your 3D Comic in your webbrowser, it's only on your machine.  This is because it is using a python local server on your machine in your blender system console. To share your 3D Comic online, you must publish it onlione just like any website. This involves geting a server and then uploading directory when you made your 3D Comic.  

(PROTIP: I use https://pages.github.com with my github account, but you can use whatever you like.  when I want to update or publish a new comic, I use githubdesktop)


---


You may also find good tips and tricks by connecting with others interested who are also making 3D Comics in these Communities:
https://www.facebook.com/groups/3dcomic/
https://www.reddit.com/r/3DComic/

You can follow me on social media here:
https://linktr.ee/spiraloid

btw, If you make anything cool with this, send me a link!
The world needs more 3D Comics.  

-bay

ps: if you want to support 3d-comics, buy a sticker, t-shirt or go pro!


https://gumroad.com/l/inkbots_sticker

https://www.amazon.com/dp/B08J2455QL

https://gumroad.com/l/3dcomictoolkit


(it's also a good idea for creator owners to think about making it easy for you fans to buy stuff if they like what you're doing,  on demand stores like gumroad, printful, zazzle, merch.amazon.com etc are an interesting option along with patreon, kofi and ntf's)

