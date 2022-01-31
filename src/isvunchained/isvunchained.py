from sys import argv
from bs4 import BeautifulSoup as BS
from os import system
from datetime import datetime
import re
import requests
import json
import time

ses = requests.Session()
auth_re = re.compile(r'.*SCLS-Token....([^"]*)".*')
txt_date = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})[^"]*')

username = []
password = []

login_url = "https://natjecaj.sczg.hr/student/login.ashx"
loginuserpass = "https://login.aaiedu.hr/sso/module.php/core/loginuserpass.php?"
application = "https://natjecaj.sczg.hr/student/login.ashx"
pay = "https://natjecaj.sczg.hr/SCSmjestaj/api/Student/UgovoriDetaljByYear"

headers = None

# proxies={'http':'http://localhost:8080', 'https':'https://localhost:8080'}
# verify=False

proxies = None
verify = True


def pull_login_info():
    global username, password
    with open("login.json", "r") as file:
        data = json.loads(file.read())
    username = data["username"]
    password = data["password"]


def login():
    global headers
    pull_login_info()

    r = ses.get(login_url, proxies=proxies, verify=verify)
    bs = BS(r.text, "html.parser")
    form = bs.find("form").get("action")
    saml_request = bs.find(attrs={"name": "SAMLRequest"}).get("value")
    data = {"SAMLRequest": saml_request}

    r = ses.post(form, data, proxies=proxies, verify=verify)
    bs = BS(r.text, "html.parser")
    auth_state = bs.find(attrs={"name": "AuthState"}).get("value")
    data = {
        "AuthState": auth_state,
        "username": username,
        "password": password,
        "Submit": "",
    }

    r = ses.post(loginuserpass, data=data, proxies=proxies, verify=verify)
    bs = BS(r.text, "html.parser")
    data = {}
    data["SAMLResponse"] = bs.find(attrs={"name": "SAMLResponse"}).get("value")
    form = bs.find("form").get("action")

    r = ses.post(form, data=data, proxies=proxies, verify=verify)
    bs = BS(r.text, "html.parser")
    form = bs.find("form").get("action")
    data = {}
    data["SAMLResponse"] = bs.find(attrs={"name": "SAMLResponse"}).get("value")

    r = ses.post(form, data=data, proxies=proxies, verify=verify)
    try:
        headers = {
            "Authorization": "Bearer "
            + str(
                auth_re.sub(
                    r"\1", [t for t in r.text.split("\n") if "SCLS-Token" in t][0]
                )
            )
        }
    except Exception:
        raise ValueError("ERROR =>>  Could not grab the Authorization token!")


def fetch():
    r = ses.get(pay, headers=headers, proxies=proxies, verify=verify)
    data = json.loads(r.text)
    return data


def check_for_pay():
    while 1:
        data = fetch()
        d = list(
            filter(lambda x: x["RacunPlacen"] and not x["IsplacenoStudentu"], data)
        )
        print(f"[{str(datetime.now())}] ==>  ", len(data), d)
        if d:
            system(
                'notify-send "Racun je uplacen!" "Cestitam! Upravo je uplacn racun na banku"'
            )
            break
        time.sleep(120)


def convert(data):
    if type(data) == list:
        for d in data:
            for t in [
                "DatumIzdavanja",
                "RacunDatum",
                "DatumUplateRacuna",
                "DatumIsplate",
                "DatumZatvaranjaRacuna",
            ]:
                if d[t]:
                    try:
                        d[t] = datetime.fromisoformat(d[t])
                    except Exception:
                        d[t] = datetime.fromisoformat(txt_date.sub(r"\1", d[t]))


def main():
    global pay
    login()

    year = str(datetime.now().year)
    if "--year" in argv:
        year = str(argv[argv.index("--year") + 1])
    pay += "?year=" + year

    data = fetch()
    if len(argv) > 1:
        if argv[1] == "-c":
            convert(data)
        if argv[1] == "-f":
            K = [d[argv[2]] for d in data if argv[2] in d]
            if "--sum" in argv:
                K = sum(K)
            print(K)
            return
    print(data)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
