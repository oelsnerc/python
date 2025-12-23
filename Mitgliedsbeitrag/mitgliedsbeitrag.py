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

class Mitglied(NamedTuple):
    mitgliedsnummer: int
    vorname: str
    nachname: str
    geburtsdatum: datetime
    aktiv: bool
    hauptzahler: int
    kategorie : Kategorie

def MemberFromRow(row: dict[str, str]) -> Mitglied:
    return Mitglied(
        mitgliedsnummer=int(row["Mitgliedsnummer"]),
        vorname=row["Vorname"],
        nachname=row["Nachname"],
        geburtsdatum=asDate(row["Geburtsdatum"]),
        aktiv=row["Status"] == "Aktivmitglied",
        hauptzahler=int(row["Hauptzahler Mitgliedsnummer"]),
        kategorie=Kategorie(row["Beitragskategorie"])
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
def getHauptzahler(members: dict[int, Mitglied]) -> dict[int, list[Mitglied]]:
    hauptzahler = {}
    for member in members.values():
        if member.hauptzahler not in hauptzahler:
            hauptzahler[member.hauptzahler] = []
        hauptzahler[member.hauptzahler].append(member)
    return hauptzahler

#------------------------------------------------------------------------------
def read_csv(file_path) -> dict[int, Mitglied]:
    members = {}
    with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';')
        for row in csvreader:
            member = MemberFromRow(row)
            members[member.mitgliedsnummer] = member
    return members

#------------------------------------------------------------------------------
argParser = argparse.ArgumentParser("CSV test")
argParser.add_argument('inp', help='csv datei', type=str)

args = argParser.parse_args()

print(f'Lese {args.inp} ...')
members = read_csv(args.inp)
print(f'Fertig. {len(members)} mitglieder geladen.')

jemand = members[2980]
# print(f'Beispiel Mitglied: [{toCSV(jemand)}] Alter: {getAge(jemand)}')

hauptzahler = getHauptzahler(members)
print(f'Anzahl Hauptzahler: {len(hauptzahler)}')

familie = hauptzahler[jemand.hauptzahler]
beitrag = calcBeitragHauptVerein_all(familie)
print(f'Beitrag Hauptverein für {jemand.vorname} {jemand.nachname}: {beitrag/100:.2f} EUR')
for mitglied in familie:
    print(f'  - {toCSV(mitglied)}')
