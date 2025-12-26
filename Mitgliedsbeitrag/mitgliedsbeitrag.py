import argparse
import csv
from typing import NamedTuple
from enum import Enum
from datetime import date, timedelta, datetime

#------------------------------------------------------------------------------
def asDate(date_str: str) -> datetime:
    days = timedelta(days=int(date_str))
    base = datetime(1899, 12, 30)
    return base + days

#------------------------------------------------------------------------------
class Kategorie(Enum):
    Alleinerziehend = 'Alleinerziehend'
    Ehepaar = 'Ehepaar/Lebensgemeinschaft'
    Familie = 'Familie'
    Student = 'Schüler/ Azubi/ Student'
    Rentner = 'Rentner'
    Mitglied = 'Mitglied'

class Abteilung(Enum):
    Tennis = 'Tennis'
    Tischtennis = 'Tischtennis'
    Turnen = 'Turnen'
    Tanzen = 'Tanzen'
    RehaSport = 'Behinderten- u. Rehasport'

class Mitglied(NamedTuple):
    mitgliedsnummer: int
    vorname: str
    nachname: str
    geburtsdatum: datetime
    aktiv: bool
    hauptzahler: int
    kategorie : Kategorie
    abteilung: Abteilung

def MemberFromRow(row: dict[str, str]) -> Mitglied:
    return Mitglied(
        mitgliedsnummer=int(row["Mitgliedsnummer"]),
        vorname=row["Vorname"],
        nachname=row["Nachname"],
        geburtsdatum=asDate(row["Geburtsdatum"]),
        aktiv=row["Status"] == "Aktivmitglied",
        hauptzahler=int(row["Hauptzahler Mitgliedsnummer"]),
        kategorie=Kategorie(row["Beitragskategorie"]),
        abteilung=Abteilung(row["Abteilung"])
    )

def toCSV(mitglied: Mitglied) -> str:
    return f'\
{mitglied.mitgliedsnummer};\
{mitglied.vorname};\
{mitglied.nachname};\
{mitglied.geburtsdatum.strftime("%Y-%m-%d")};\
{mitglied.kategorie}'

def getAge(member: Mitglied) -> int:
    today = date.today()
    age = today.year - member.geburtsdatum.year - \
        ((today.month, today.day) < (member.geburtsdatum.month, member.geburtsdatum.day))
    return age

def isHauptzahler(member: Mitglied) -> bool:
    return member.mitgliedsnummer == member.hauptzahler

def isKind(member: Mitglied) -> bool:
    return getAge(member) < 18

def findHauptzahler(hauptzahlerNummer: int, familie: list[Mitglied]) -> Mitglied | None:
    return next((member for member in familie if member.mitgliedsnummer == hauptzahlerNummer), None)

#------------------------------------------------------------------------------
def calcBeitragHauptVerein_single(member: Mitglied) -> int:
    if member.aktiv == False: return 3000

    if isKind(member): return 5500

    if member.kategorie == Kategorie.Rentner: return 7200
    if member.kategorie == Kategorie.Student: return 5500
    if member.kategorie == Kategorie.Familie:
        if isHauptzahler(member): return 16500
        else: return 0

    return 8500

def calcBeitragHauptVerein_all(members: list[Mitglied]) -> int:
    return sum(calcBeitragHauptVerein_single(member) for member in members)

#------------------------------------------------------------------------------
def read_csv(file_path) -> tuple[dict[int, Mitglied], dict[int, list[Mitglied]]]:
    members = {}
    hauptzahler = {}
    with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';')
        for row in csvreader:
            member = MemberFromRow(row)
            members[member.mitgliedsnummer] = member
            if member.hauptzahler not in hauptzahler:
                hauptzahler[member.hauptzahler] = []
            hauptzahler[member.hauptzahler].append(member)
    return members, hauptzahler

#------------------------------------------------------------------------------
def writeMemberCSV(csvwriter, hauptZahlerNummer: str, member: Mitglied, hauptvereinBeitrag: int) -> None:
    csvwriter.writerow({
        'Hauptzahler': hauptZahlerNummer,
        'Vorname': member.vorname,
        'Nachname': member.nachname,
        'Mitgliedsnummer': member.mitgliedsnummer,
        'Abteilung': member.abteilung.value,
        'Status': 'aktiv' if member.aktiv else 'passiv',
        'Alter': getAge(member),
        'Beitragskategorie': member.kategorie.value,
        'Hauptverein': hauptvereinBeitrag
    })

def writeHauptzahlerCSV(csvwriter, hauptZahler: Mitglied, familie: list[Mitglied]) -> None:
    hauptvereinBeitrag = calcBeitragHauptVerein_all(familie)
    writeMemberCSV(csvwriter, str(hauptZahler.mitgliedsnummer), hauptZahler, hauptvereinBeitrag)

def writeFamilienCSV(csvwriter, familie: list[Mitglied]) -> None:
    if len(familie) < 2: return
    for member in familie:
        writeMemberCSV(csvwriter, '    ', member, calcBeitragHauptVerein_single(member))

def write_csv(file_path, hauptzahlerListe: dict[int, list[Mitglied]]) -> None:
    with open(file_path, mode='w', encoding='utf-8-sig', newline='') as csvfile:
        fieldnames = ['Hauptzahler', 'Vorname', 'Nachname', 'Mitgliedsnummer', 'Abteilung', 'Status', 'Alter', 'Beitragskategorie', 'Hauptverein']
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        csvwriter.writeheader()

        for hauptZahlerNummer, familie in hauptzahlerListe.items():
            hauptZahler = findHauptzahler(hauptZahlerNummer, familie)
            if hauptZahler is None:
                print(f'Warnung: Kein Hauptzahler mit Mitgliedsnummer {hauptZahlerNummer} gefunden.')
                continue

            writeHauptzahlerCSV(csvwriter, hauptZahler, familie)
            if args.debug:
                writeFamilienCSV(csvwriter, familie)

#------------------------------------------------------------------------------
argParser = argparse.ArgumentParser("CSV test")
argParser.add_argument('-i', '--input', help='Mitgliederliste als csv Datei', type=str, required=True)
argParser.add_argument('-o', '--output', help='Ergebnis der Beitragsliste als csv Datei', type=str, required=True)
argParser.add_argument('-d', '--debug', help='Schreib Familien in die Beitragsliste', action='store_true')

args = argParser.parse_args()

print(f'Lese {args.input} ...')
members, hauptzahler = read_csv(args.input)
print(f'Anzahl Mitglieder : {len(members)}')
print(f'Anzahl Hauptzahler: {len(hauptzahler)}')

print(f'Schreibe {args.output} ...')
write_csv(args.output, hauptzahler)
