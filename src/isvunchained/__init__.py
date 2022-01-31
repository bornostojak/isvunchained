"""Top-level package for ISVUnchained."""

from .client import *

__author__ = """Borno Stojak"""
__email__ = "borno.stojak@gmail.com"
__version__ = "0.2.0"


def main(username: str = None, password: str = None, autologin: bool = True):
    year = None

    try:
        if argv[1] == "saldo":
            with open(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "login.json"),
                "r",
            ) as file:
                login = json.loads(file.read())

            c = Client(**login)
            c.login()
            page = c.get("https://issp.srce.hr/Student").text
            bs = BS(page, "html.parser")

            print("saldo" in page)
            stanje = {}
            for s in ["Razina prava", "Raspoloživi saldo", "Potrošeno danas"]:
                stanje[s] = bs.find(text=s).parent.parent.findAll("p")[1].text
            os.system(
                'notify-send "Stanje na iksici:" "{}"'.format(
                    "\n".join([k + ": " + stanje[k] for k in stanje.keys()])
                )
            )

            return
    except IndexError:
        pass

    if username and password:
        c = Client(username=username, password=password, autologin=autologin)
    else:
        c = Client(autologin=True)

    if "--year" in argv:
        year = str(argv[argv.index("--year") + 1])

    data = c.fetch_pay_data(year)
    if "--pdf" in argv:
        pdf_links = []
        for link in Client.get_contract_pdf_link(data):
            if requests.get(link).status_code == 200:
                pdf_links.append(link)
        print("\n".join(pdf_links))
        return

    if len(argv) > 1:
        if argv[1] == "-c":
            Client.convert(data)
        if argv[1] == "-f":
            K = [d[argv[2]] for d in data if argv[2] in d]
            if "--sum" in argv:
                K = sum(K)
            print(K)
            return
    print(data)
