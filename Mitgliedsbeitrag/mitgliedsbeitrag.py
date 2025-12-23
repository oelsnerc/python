import argparse
import csv
from typing import NamedTuple
from datetime import date, timedelta, datetime

#------------------------------------------------------------------------------
def asDate(date_str: str) -> datetime:
    days = timedelta(days=int(date_str))
    base = datetime(1899, 12, 30)
    return base + days

#------------------------------------------------------------------------------
class Mitglied(NamedTuple):
    mitgliedsnummer: int
    vorname: str
    nachname: str
    geburtsdatum: datetime
    hauptzahler: int = 0

def MemberFromRow(row: dict[str, str]) -> Mitglied:
    return Mitglied(
        mitgliedsnummer=int(row["Mitgliedsnummer"]),
        vorname=row["Vorname"],
        nachname=row["Nachname"],
        geburtsdatum=asDate(row["Geburtsdatum"]),
        hauptzahler=int(row["Hauptzahler Mitgliedsnummer"])
    )

def toCSV(mitglied: Mitglied) -> str:
    return f'\
{mitglied.mitgliedsnummer};\
{mitglied.vorname};\
{mitglied.nachname};\
{mitglied.geburtsdatum.strftime("%Y-%m-%d")};\
{mitglied.hauptzahler}'

def getAge(member: Mitglied) -> int:
    today = date.today()
    age = today.year - member.geburtsdatum.year - \
        ((today.month, today.day) < (member.geburtsdatum.month, member.geburtsdatum.day))
    return age

def isKind(member: Mitglied) -> bool:
    return getAge(member) < 18

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
print(f'Beispiel Mitglied: [{toCSV(jemand)}] Alter: {getAge(jemand)}')
