## Running
Project is based on Python3. It is recommended to use version not older than 3.3.
### Creating virtual environment
Python3 has build in module `venv`. Create virtual environment `expander` dedicated for this project.
```
py -m venv expander
```
The environment will be created at `C:\Users\YourUsername\Envs\expander`
In order to start using it, you need to activate it:
```
.\expander\Scripts\activate
```
Now install packages below:
```
pip install django
pip install django-bulma
pip install django-jquery-ui
pip install requests
pip install SPARQLWrapper
pip install pytictoc
```
### Running application
Activate your previously prepared virtual environment or if it is already activated skip this step
```
.\expander\Scripts\activate
```
Locate folder with your code, eg. `E:\SetExpander`, navigate to it and run the app
```
cd E:\SetExpander
py manage.py runserver
```
In your browser navigate to [http://127.0.0.1:8000/expander/](http://127.0.0.1:8000/expander/) and enjoy the app
