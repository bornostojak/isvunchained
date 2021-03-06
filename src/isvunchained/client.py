from sys import argv
from bs4 import BeautifulSoup as BS
from os import system
from datetime import datetime
from os.path import exists
import re
import requests
import json
import time

auth_re = re.compile(r'.*SCLS-Token....([^"]*)".*')
txt_date = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})[^"]*')

username = []
password = []

application = "https://natjecaj.sczg.hr/student/login.ashx"


# proxies={'http':'http://localhost:8080', 'https':'https://localhost:8080'}
# verify=False


class Client(object):
    """
    The scraper client used to connect to tje ISVU server and log in.
    """

    login_url = natjecaj_url = "https://natjecaj.sczg.hr/student/login.ashx"
    issp_url = "https://issp.srce.hr/account/loginaai"
    loginuserpass_url = "https://login.aaiedu.hr/sso/module.php/core/loginuserpass.php?"
    pay_url = "https://natjecaj.sczg.hr/SCSmjestaj/api/Student/UgovoriDetaljByYear"
    contract_pdf_url = "https://natjecaj.sczg.hr/SCSmjestaj/api/pdf/Ugovor"

    login_pages={
        'natjecaj.sczg.hr': natjecaj_url,
        'issp.srce.hr': issp_url
    }

    def __init__(
        self,
        username: str = None,
        password: str = None,
        headers: dict = None,
        proxies: dict = None,
        verify: bool = True,
        autologin=False,
    ):
        self.username = username
        self.password = password
        self.headers = headers
        self.proxies = proxies
        self.session = requests.Session()
        self.verify = verify
        self.logget_in = False
        if (not self.username or not self.password) and exists("login.json"):
            self.__pull_login_info()

        if autologin:
            self.login()

    def login(self, debug=False):
        self.headers

        # r = self.session.get(Client.login_url, proxies=self.proxies, verify=self.verify)
        # r = self.autoresolve(r, debug)
        r = self.get(Client.login_url)

        try:
            r = self.autoresolve(r)
        except Exception:
            raise ValueError("ERROR =>>  Could not grab the Authorization token!")

        self.logged_in = True

    def __pull_login_info(self):
        if not exists("login.json") and not self.username and not self.password:
            raise ValueError(
                'The login information are missing!\nPlease provide login info inside of a "login.json" file \
or pass the data into the constructor'
            )
        with open("login.json", "r") as file:
            data = json.loads(file.read())
        self.username = data["username"]
        self.password = data["password"]

    def resolve_saml_request(self, r, debug=False):
        if type(r) is requests.models.Response:
            bs = BS(r.text, "html.parser")
        elif type(r) is str:
            bs = BS(r, "html.parser")

        form = bs.find("form").get("action")
        saml_request = bs.find(attrs={"name": "SAMLRequest"}).get("value")
        data = {"SAMLRequest": saml_request}

        r = self.session.post(form, data, proxies=self.proxies, verify=self.verify)
        return r

    def resolve_saml_response(self, req, debug=0):
        if type(req) is requests.models.Response:
            bs = BS(req.text, "html.parser")
        elif type(req) is str:
            bs = BS(req, "html.parser")

        data = {}
        data["SAMLResponse"] = bs.find(attrs={"name": "SAMLResponse"}).get("value")
        form = bs.find("form").get("action")

        result = self.session.post(
            form, data=data, proxies=self.proxies, verify=self.verify
        )
        return result

    def resolve_auth_state(self, req, debug=0):
        if type(req) is requests.models.Response:
            bs = BS(req.text, "html.parser")
        elif type(r) is str:
            bs = BS(req, "html.parser")

        auth_state = bs.find(attrs={"name": "AuthState"}).get("value")
        data = {
            "AuthState": auth_state,
            "username": self.username,
            "password": self.password,
            "Submit": "",
        }

        result = self.session.post(
            Client.loginuserpass_url,
            data=data,
            proxies=self.proxies,
            verify=self.verify,
        )
        return result

    def autoresolve(self, req, debug=0):
        if "SAMLRequest" in req.text:
            if debug:
                print("Resolving SAMLRequest...")
            return self.autoresolve(self.resolve_saml_request(req, debug), debug)
        elif "SAMLResponse" in req.text:
            if debug:
                print("Resolving SAMLResponse...")
            return self.autoresolve(self.resolve_saml_response(req, debug), debug)
        elif "AuthState" in req.text:
            if debug:
                print("Resolving AuthState...")
            return self.autoresolve(self.resolve_auth_state(req, debug), debug)
        if "SCLS-Token" in req.text and (not self.headers or "Authorization" not in self.headers):
            self.headers = {
                "Authorization": "Bearer "
                + str(
                    auth_re.sub(
                        r"\1", [t for t in req.text.split("\n") if "SCLS-Token" in t][0]
                    )
                )
            }
        return req

    def fetch_pay_data(self, year: str = None, inplace: bool = False):
        if '-' in str(year):
            st,ed = year.split('-')[:2]
            try:
                st = int(st)
                ed = datetime.now().year if not ed else int(ed) 
                
                if st>=ed: raise Exception("MN")
                
                return [dt for yr in range(st, ed+1)[::-1] for dt in self.fetch_pay_data(yr)]
            except Exception as e:
                return
            
            print("Format year with [lower year]-[*higher year or empty]")
            return return_data
        if not year:
            year = str(datetime.now().year)
        

        if 'natjecaj.sczg.hr' not in {cookie.domain for cookie in self.session.cookies}:
            self.get(self.natjecaj_url)

        r = self.get(f"{Client.pay_url}?year={str(year)}", 1)
        data = json.loads(r.text)
        if not inplace:
            return data
        else:
            self.paydata = data

    def get(self, url: str, debug: bool = False):
        return self.autoresolve(
            self.session.get(url,
            headers=self.headers,
            proxies=self.proxies,
            verify=self.verify,
        ), debug)

    @staticmethod
    def get_contract_pdf_link(data):
        rez = []
        for contract in data if type(data) is list else [data]:
            if type(contract) is dict:
                rez.append(
                    Client.contract_pdf_url
                    + "/{}/{}/{}".format(
                        contract["UgovorBroj"],
                        contract["DProtocolID"],
                        contract["Signature"],
                    )
                )
        return rez

    @staticmethod
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
                            if type(d[t]) is datetime: return
                            d[t] = datetime.fromisoformat(d[t].split('.')[0])
                        except Exception as e:
                            d[t] = datetime.fromisoformat(txt_date.sub(r"\1", d[t].split('.')[0])) #if '.' in d[t] else ))