## Running
Project is based on Python3. It is recommended to use version not older than 3.3.
### Creating virtual environment
Python3 has build in module `venv`. Create virtual environment `expander` dedicated for this project.
```
python -m venv expander
```
The environment will be created at `C:\Users\YourUsername\Envs\expander`
In order to start using it, you need to activate it:
```
.\expander\Scripts\activate
```
Now install packages below:
```
pip install -r requirements.txt
```
### Running application
Activate your previously prepared virtual environment or if it is already activated skip this step
```
.\expander\Scripts\activate
```
Locate folder with your code, eg. `E:\SetExpander`, navigate to it and run the app
```
cd E:\SetExpander
python manage.py runserver
```
In your browser navigate to [http://127.0.0.1:8000/expander/](http://127.0.0.1:8000/expander/) and enjoy the app

Before first run the database initialization is necessary: ``python manage.py migrate``
### Running tests
Change current directory to where manage.py file is, than run:
```
python manage.py tests
```

## Settings

All settings are in ``settings.py`` file. 
Project to work needs own BABELNET_API_KEY. 

There are few configurable settings to help with development.

MEASURE_TIME - print execution time of the functions annotated with @timing

SILKY_PYTHON_PROFILER, SILKY_PYTHON_PROFILER_BINARY, SILKY_PYTHON_PROFILER_RESULT_PATH - settings related with silk plugin, which keep stacktrace to optimize services, when enabled can be executed at [http://127.0.0.1:8000/silk/]([http://127.0.0.1:8000/silk/])