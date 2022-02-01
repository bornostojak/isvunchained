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
parser.add_argument("-y", "--year", metavar="YEAR", type=str, help="The year")
parser.add_argument(
    "-o", 
    "--options", 
    metavar="OPTIONS", 
    type=str, 
    help="Aditional options [latest, last_paid, total, raw, iksica, pdf, pay]"
)
parser.add_argument(
    "-n", "--neat", action="store_true", help="Print neatly separated values"
)
parser.add_argument(
    "-P", "--pretty", action="store_true", help="Print pretty output"
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

    fetched_data = c.fetch_pay_data(args.year)
    if not fetched_data:
        exit(1)
    data = {
        "data": fetched_data,
        "client": c,
        "args": args
    }
    
    for option in args.options[:-1]:
        neat(option)
        process_options(option, **data)

    neat(args.options[-1])
    process_options(args.options[-1], **data)


def process_options(current_option, data, client, args):
    if "iksica" == current_option:
        page = client.get(
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

    if "pdf" == current_option:
        pdf_links = []
        for link in Client.get_contract_pdf_link(data):
            if requests.get(link).status_code == 200:
                pdf_links.append(link)

        print("\n".join(pdf_links))
        return

    export_data = [*data]

    if "raw" == current_option or "sirovo" == current_option:
        print(data)

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

    if current_option == "last_paid":
        srt = sorted(
            [g for g in client.fetch_pay_data(args.year) if g['UgovorIsplacen']],
            key= lambda x: x['DatumIsplate'], 
            reverse=True
            )
        format_raw(srt[0], args.pretty)

    if current_option == "latest":
        srt = list(sorted(
            [g for g in client.fetch_pay_data(args.year) if g['RacunDatum']],
            key= lambda x: x['RacunDatum'], 
            reverse=True
            ))
        format_raw(srt[0], args.pretty)


def format_raw(raw_data, pretty):
    if not pretty:
        print(raw_data)
        return
    
    if type(raw_data) is dict:
        raw_data=[raw_data]
    length = max([len(k) for k in raw_data[0].keys()])+3
    
    print("\n".join([
        f"Ugovor: {ugovor['UgovorBroj']}\n"+
        "\n".join([f" {k}{'.'*(length-len(k))} {v}" for k,v in ugovor.items() if k != "UgovorBroj"])+
        "\n"
        for ugovor in raw_data]))