Passerelle connector with BOSA services 
=======================================

This passerelle is meant to be connected to BOSA using iMio API Microservices 
(APIMS).

Installation
------------

 - add to Passerelle installed apps settings:
   INSTALLED_APPS += ('passerelle_imio_bosa',)

 - enable module:
   PASSERELLE_APP_PASSERELLE_IMIO_BOSA_ENABLED = True


Usage
-----

 - create and configure new connector
   - Title/description: whatever you want

 - test service by clicking on the available links
   - the /test/ endpoint to test the connection with APIMS
