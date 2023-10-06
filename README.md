# scopetrak
Dobsonian "guiding" system with Flask Interface

CURRENT STATUS: In active development, no release version available

This software is intended for installation on an INDI based computer controlling a Dobsonian telescope equipped with a GOTO system. 
In my case I have a 16" F/4.5 telescope with an OnStep drive system, which is operated by a Raspberry Pi 4 running the Stellarmate OS. 

The use case for this software is when using GOTO to position a telescope, the final position is generally off by potentially a fair bit. 
This software will detect that a telescope has moved (slewed), and start doing plate solves to detect whether the telescope is actually 
centered on the desired coordinates. To do this an image is taken (either from the main telescope or a guide scope with a camera intended 
for this purpose) of the sky and it is plate solved to determine the actual position of the telescope. If there is a meaningful difference,
the telescope is slewed to where it thinks the correct position is, and another solve is done. This repeats until the scope is within a specified 
minimum tolerance (set to 30 arcsecs) whereupon the coordinates will be sync'd to the telescope. Solves can continue to be done in case the user 
bumps the telescope (often the case at star parties etc.) whereupon the scope will return to the correct position.

Solving can be turned on and off with a Flask application accessed via a web browser. The Flask application is intended to be used on a phone or 
similar small format screen. 

INDI and ASTAP is required as a separate installations
