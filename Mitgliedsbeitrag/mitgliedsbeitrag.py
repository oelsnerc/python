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
    Wandern = 'Wandern'

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

def getHauptzahler(familie: list[Mitglied]) -> Mitglied:
    hauptzahler =  next((member for member in familie if member.mitgliedsnummer == member.hauptzahler), None)
    if hauptzahler is None:
        raise ValueError(f'Kein Hauptzahler in der Familie gefunden\n{[toCSV(m) for m in familie]}')
    return hauptzahler

#------------------------------------------------------------------------------
# * Tennis Aktiv                  >= 18 Jahre             15500 Mitglied
# * Tennis Aktiv                  < 18 Jahre               9600 Mitglied
# * Tennis Aktiv  Ehepaare                                28000 Hauptzahler
# * Tennis Aktiv  Student         < 27 Jahre               9600 Mitglied
# * Tennis Aktiv  Familie         2 Erwachsene + 1 Kind   30000 Hauptzahler
# * Tennis Aktiv  Familie         weitere Kinder           4000 Hauptzahler
# * Tennis Aktiv  Alleinerziehend 1 Erwachsener + 1 Kind  20000 Hauptzahler
# * Tennis Aktiv  Alleinerziehend weitere Kinder           4000 Hauptzahler
#   Tennis Aktiv                  >= 16 Jahre              4500 Mitglied    <---- Not used?
# * Tennis Passiv                 < 14 Jahre                600 Mitglied
# * Tennis Passiv                 < 18 Jahre               1800 Mitglied
# * Tennis Passiv                 >= 18 Jahre              2900 Mitglied
# * Tennis Passiv Student                                  1800 Hauptzahler
#------------------------------------------------------------------------------
def calcBeitragTennis_passive(member: Mitglied) -> int:
    if member.kategorie == Kategorie.Student: return 1800
    age = getAge(member)
    if age < 14: return 600
    if age < 18: return 1800
    return 2900

def calcBeitragTennis_familie(member: Mitglied) -> int:
    beitragKind = 4000
    if isKind(member): return beitragKind
    if isHauptzahler(member): return 30000 - beitragKind
    return 0    # the other adult in the family

def calcBeitragTennis_singleParent(member: Mitglied) -> int:
    beitragKind = 4000
    if isHauptzahler(member): return 20000 - beitragKind
    # if isKind(member): return beitragKind
    # raise ValueError(f'Alleinerziehend und weiterer Erwachsener? {toCSV(member)}')
    return beitragKind  # for the child (not matter the age)

def calcBeitragTennis_single(member: Mitglied) -> int:
    if member.aktiv == False: return calcBeitragTennis_passive(member)

    # active members only
    if member.kategorie == Kategorie.Student:
        if getAge(member) < 27: return 9600
        else: return 15500

    if member.kategorie == Kategorie.Ehepaar:
        if (isHauptzahler(member)): return 28000
        else: return 0  # the other half of the couple

    if member.kategorie == Kategorie.Familie:
        return calcBeitragTennis_familie(member)
    
    if member.kategorie == Kategorie.Alleinerziehend:
        return calcBeitragTennis_singleParent(member)
    
    if isKind(member): return 9600
    return 15500

#------------------------------------------------------------------------------
# Tischtennis Aktiv < 18 Jahre      6000 Mitglied
# Tischtennis Aktiv >= 18 Jahre     8000 Mitglied
#------------------------------------------------------------------------------
def calcBeitragTischtennis_single(member: Mitglied) -> int:
    if member.aktiv == False: return 0

    if isKind(member): return 6000
    return 8000

#------------------------------------------------------------------------------
# Wandern Aktiv                     3500 Mitglied
#------------------------------------------------------------------------------
def calcBeitragWandern_single(member: Mitglied) -> int:
    if member.aktiv == False: return 0
    return 3500 

#------------------------------------------------------------------------------
def calcBeitragAbteilung_single(member: Mitglied) -> int:
    if member.abteilung == Abteilung.Tennis: return calcBeitragTennis_single(member)
    if member.abteilung == Abteilung.Tischtennis: return calcBeitragTischtennis_single(member)
    if member.abteilung == Abteilung.Wandern: return calcBeitragWandern_single(member)

    if member.abteilung in {Abteilung.Turnen, Abteilung.Tanzen, Abteilung.RehaSport}:
        print(f'Beitragsberechnung für Abteilung {member.abteilung.value} nicht implementiert {toCSV(member)}')
        return 0
    raise ValueError(f'Unbekannte Abteilung {member.abteilung} für Mitglied {toCSV(member)}')

def calcBeitragAbteilung_all(familie: list[Mitglied]) -> int:
   return sum(calcBeitragAbteilung_single(member) for member in familie)

#------------------------------------------------------------------------------
# Hauptverein Aktiv           < 18 Jahre                                   5500   Mitglied
# Hauptverein Aktiv           >= 18 Jahre                                  8500   Mitglied
# Hauptverein Aktiv   Student                                              5500   Mitglied
# Hauptverein Aktiv   Rentner >=65 Jahre                                   7200   Mitglied
# Hauptverein Aktiv   Familie beide Eltern mit mind 1 minderjährigen Kind 16500   Hauptzahler
# Hauptverein Passiv                                                       3000   Mitglied
#------------------------------------------------------------------------------
def calcBeitragHauptVerein_single(member: Mitglied) -> int:
    if member.aktiv == False: return 3000

    if member.kategorie == Kategorie.Student: return 5500

    if member.kategorie == Kategorie.Rentner:
        if getAge(member) >= 65: return 7200
        else: return 8500

    if member.kategorie == Kategorie.Familie:
        if isHauptzahler(member): return 16500
        else: return 0

    if isKind(member): return 5500
    return 8500

def calcBeitragHauptVerein_all(familie: list[Mitglied]) -> int:
    return sum(calcBeitragHauptVerein_single(member) for member in familie)

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
def writeMemberCSV(csvwriter, hauptZahlerNummer: str, member: Mitglied, hauptvereinBeitrag: int, abteilungBeitrag: int) -> None:
    csvwriter.writerow({
        'Hauptzahler': hauptZahlerNummer,
        'Vorname': member.vorname,
        'Nachname': member.nachname,
        'Mitgliedsnummer': member.mitgliedsnummer,
        'Abteilung': member.abteilung.value,
        'Status': 'aktiv' if member.aktiv else 'passiv',
        'Alter': getAge(member),
        'Beitragskategorie': member.kategorie.value,
        'Hauptverein': hauptvereinBeitrag,
        'Abteilung': abteilungBeitrag,
        'Gesamt': hauptvereinBeitrag + abteilungBeitrag
    })

def writeHauptzahlerCSV(csvwriter, hauptZahler: Mitglied, familie: list[Mitglied]) -> None:
    hauptvereinBeitrag = calcBeitragHauptVerein_all(familie)
    abteilungBeitrag = calcBeitragAbteilung_all(familie)
    writeMemberCSV(csvwriter, str(hauptZahler.mitgliedsnummer), hauptZahler, hauptvereinBeitrag, abteilungBeitrag)

def writeFamilienCSV(csvwriter, familie: list[Mitglied]) -> None:
    if len(familie) < 2: return
    for member in familie:
        writeMemberCSV(csvwriter, '    ', member, calcBeitragHauptVerein_single(member), calcBeitragAbteilung_single(member))

def write_csv(file_path, hauptzahlerListe: dict[int, list[Mitglied]]) -> None:
    with open(file_path, mode='w', encoding='utf-8-sig', newline='') as csvfile:
        fieldnames = ['Hauptzahler', 'Vorname', 'Nachname', 'Mitgliedsnummer', 'Abteilung', 'Status', 'Alter', 'Beitragskategorie', 'Hauptverein', 'Abteilung', 'Gesamt']
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        csvwriter.writeheader()

        for familie in hauptzahlerListe.values():
            hauptZahler = getHauptzahler(familie)

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
