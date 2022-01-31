"""Top-level package for ISVUnchained."""

from .client import *
import os
from argparse import ArgumentParser

__author__ = """Borno Stojak"""
__email__ = "borno.stojak@gmail.com"
__version__ = "0.2.0"

parser = ArgumentParser()
parser.add_argument(
    "-u",
    "--username",
    metavar="USERNAME",
    type=str,
    help="The username for the account",
)
parser.add_argument(
    "-p",
    "--password",
    metavar="PASSWORD",
    type=str,
    help="The password for the account",
)
parser.add_argument("-y", "--year", metavar="YEAR", type=int, help="The year")
parser.add_argument(
    "-o", "--options", metavar="OPTIONS", type=str, help="Aditional options"
)
parser.add_argument(
    "-n", "--neat", action="store_true", help="Print neatly separated values"
)


def main(username: str = None, password: str = None, autologin: bool = True):
    args = parser.parse_args()
    args.options = (
        [op.lower() for op in args.options.split(",")] if args.options else []
    )

    neat = (
        lambda intermezzo: print(
            f"\n{'-'*int((60-len(intermezzo))/2)} {intermezzo[0].upper()}{intermezzo[1:].lower()} {'-'*int((60-len(intermezzo))/2)}{'-'*(len(intermezzo)%2)}\n"
        )
        if args.neat
        else ""
    )

    username = username if not args.username else args.username
    password = password if not args.password else args.password

    if username and password:
        c = Client(username=username, password=password, autologin=autologin)
    else:
        c = Client(autologin=True)

    data = {
        "data": c.fetch_pay_data(args.year),
        "username": username,
        "password": password,
        "year": args.year,
    }
    
    for option in args.options[:-1]:
        process_options(option, **data)
        neat(option)
    process_options(args.options[-1], **data)


def process_options(current_option, data, username, password, year):
    if "iksica" == current_option:
        try:
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "login.json"
            )
            if os.path.exists(filepath):
                with open(
                    filepath,
                    "r",
                ) as file:
                    login = json.loads(file.read())
            else:
                login = {"username": username, "password": password, "autologin": 0}

            cl = Client(**login)
            page = cl.get(
                "https://issp.srce.hr/account/loginaai", debug="debug" == current_option
            ).text
            bs = BS(page, "html.parser")

            stanje = {}
            for s in ["Razina prava", "Raspoloživi saldo", "Potrošeno danas"]:
                stanje[s] = [*bs.find(text=s).parent.parent.children][-2].text
            # os.system(
            #'notify-send "Stanje na iksici:" "{}"'.format(
            # "\n".join([k + ": " + stanje[k] for k in stanje.keys()])
            # )
            # )
            print("\n".join([f"{k}: {v}" for k, v in stanje.items()]))
        except IndexError:
            pass
        finally:
            del cl

    if "pdf" == current_option:
        pdf_links = []
        for link in Client.get_contract_pdf_link(data):
            if requests.get(link).status_code == 200:
                pdf_links.append(link)

        print("\n".join(pdf_links))
        return

    export_data = [*data]

    if "convert" == current_option:
        Client.convert(export_data)
    if "pay" == current_option:
        temp_data = [*data]
        Client.convert(temp_data)

        for month in temp_data:
            if not month["RacunDatum"]:
                continue
            month_name = month["RacunDatum"].strftime("%B")
            print(
                f"{month['RacunDatum'].year} {month_name}{'.'*(12-len(month_name))} {0.0 if not month['IsplacenoStudentu'] else month['IsplacenoStudentu']:.2f} kn"
            )
        del temp_data

    if "total" == current_option:
        print(
            f"Plaća: {round(sum([each['IsplacenoStudentu'] for each in export_data if each['IsplacenoStudentu']]),2)} kn"
        )
        print(
            f"Porez: {round(sum([each['Porez'] for each in export_data if each['Porez']]),2)} kn"
        )
        print(
            f"Prirez: {round(sum([each['Prirez'] for each in export_data if each['Prirez']]),2)} kn"
        )

    if "raw" == current_option or "sirovo" == current_option:
        print(data)
