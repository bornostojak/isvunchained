#!/bin/python3

from bs4 import BeautifulSoup as BS
from .cliend import Client
import os, json

with open(os.path.join(os.path.dirname(payday.__path__), "login.json"), "r") as file:
    login = json.loads(file.read())

c = Client(**login)
c.login()

BS(c.get("https://issp.srce.hr/Student"))
