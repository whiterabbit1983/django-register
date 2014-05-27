========
Register
========

Register is a Django application to register new users.

Quick start
-----------

1. Add "register" to your INSTALLED_APPS settings:
   
      INSTALLED_APPS = (
          ...
          "register",
          ...
      )

2. Run `python manage.py syncdb` to create new user models.
   Note, that you have to run syncdb first time after you included register to INSTALLED_APPS,
   because this application uses custom User model. Read Django manual for details.

3. Include the register URLconf in your project urls.py like this:
   url(r'^register/', include("register.urls"))

4. Optionally add REGISTER_ACTIVATION_SUBJECT and/or REGISTER_FROM_EMAIL to your settings.py.
   REGISTER_ACTIVATION_SUBJECT sets a subject of a confirmation email
    
   Example: REGISTER_ACTIVATION_SUBJECT = "Activation code"

   REGISTER_FROM_EMAIL sets a "From" field of a confirmation email 

   Example: REGISTER_FROM_EMAIL = "noreply@example.com"

5. If you want to customise templates, see examples in "register/templates" directory.
