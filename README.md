TARUMT App API
==============

Use TARUMT app... *but in Python!*

---

This library provides an api interface to the endpoints used in the TARUMT app.

***Note: This library is WIP***

Requirements
------------

- [Python 3.12.0](https://www.python.org/downloads/) or above
- requests

Usage
-----

To use the API, import it and login with your username and password.

Example: 

```python
from tarumt_app_api import TarAppAPI

tar_api = TarAppAPI()
tar_api.login("username", "password")

from pprint import pprint
pprint(tar_api._fetch_class_timetable().json())
```

So far the library only returns the raw responses, but it will be slowly developed for higher level. 

Developing
----------

### Installing

1. Clone the repo
   ```shell
   git clone https://github.com/makan-kencing/tarumt-app-api.git
   cd tarumt-app-api
   ```
2. Create a virtualenv
   ```shell
   virtualenv venv
   
   venv/Scripts/activate     # on windows
   # OR
   source venv/bin/activate  # on unix systems 
   ```
3. Install pip dependencies
   ```shell
   pip install -r requirements.txt
   ```

Ending notes
------------

This library is NOT affiliated with Tunku Abdul Rahman University of Management and Technology (TARUMT) or any similar entities.
