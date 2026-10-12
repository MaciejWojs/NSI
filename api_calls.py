"""
Eksploracyjne wywolania SUT (BankSystem) — Lab NSI, punkt 5.
Przed kazdym wywolaniem wypisywane jest oczekiwane zachowanie.
Wynik sesji (do wskaźników w sprawozdaniu) trafia do wywolania.json.
"""

import json
from datetime import date
from pathlib import Path

from API import (
    BankSystem,
    ZewnetrznyProcesor,
)

N_OK_A = "1234567895"  # 45 % 10 = 5
N_OK_B = "1111111119"  # 9 % 10 = 9
N_OK_C = "0000000000"  # 0 % 10 = 0
N_OK_D = "2222222228"  # 18 % 10 = 8

ROOT = Path(__file__).resolve().parent
KOD = ROOT / "raporty" / "NSI_RAPORT_1" / "kod"


def _tekst(wynik):
    if isinstance(wynik, Exception):
        return f"{type(wynik).__name__}: {wynik}"
    if hasattr(wynik, "numer") and hasattr(wynik, "saldo"):
        return (
            f"Konto {wynik.numer}, saldo={wynik.saldo}, wlasciciel={wynik.wlasciciel!r}"
        )
    return repr(wynik)


def main():
    bs = BankSystem()
    dzisiaj = date.today()
    n = 0
    wyniki = []

    def N(opis, oczekiwane, fn, *, awaria=False, przyczyna=None, dotkliwosc=None):
        nonlocal n
        n += 1
        print(f"\n--- #{n}: {opis} ---")
        print(f"  OCZEKIWANE: {oczekiwane}")
        try:
            tekst = _tekst(fn())
        except Exception as e:
            tekst = _tekst(e)
        print(f"  FAKTYCZNE: {tekst}")
        wyniki.append(
            {
                "nr": n,
                "opis": opis,
                "oczekiwane": oczekiwane,
                "faktyczne": tekst,
                "awaria": awaria,
                "przyczyna": przyczyna,
                "dotkliwosc": dotkliwosc,
            }
        )

    N(
        "utworz_konto A, saldo 1000",
        "Konto A, saldo 1000, wlasciciel Anna Kowalska",
        lambda: bs.utworz_konto(N_OK_A, "Anna Kowalska", 1000),
    )
    N(
        "utworz_konto B, saldo 500",
        "Konto B, saldo 500, wlasciciel Jan Nowak",
        lambda: bs.utworz_konto(N_OK_B, "Jan Nowak", 500),
    )
    N(
        "wplac(A, 100)",
        "saldo A = 1100",
        lambda: bs.wplac(N_OK_A, 100),
    )

    N(
        "utworz_konto numer pusty",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto("", "X", 0),
    )
    N(
        "utworz_konto numer None",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto(None, "X", 0),
    )
    N(
        "utworz_konto znaki specjalne",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto("!@#$%^&*()", "X", 0),
    )
    N(
        "utworz_konto za krotki",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto("12345", "X", 0),
    )
    N(
        "utworz_konto zla suma kontrolna",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto("1234567890", "X", 0),
    )
    N(
        "utworz_konto z literami",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto("123456789A", "X", 0),
    )
    N(
        "utworz_konto numer jako int",
        "ValueError: Nieprawidlowy numer konta",
        lambda: bs.utworz_konto(1234567895, "X", 0),
    )

    N(
        "utworz_konto C, wlasciciel pusty",
        "Konto C powstaje, wlasciciel pusty, saldo 0",
        lambda: bs.utworz_konto(N_OK_C, "", 0),
    )
    N(
        "utworz_konto D, wlasciciel specjalny, saldo -50",
        "Konto D powstaje, saldo -50 (opis nie odrzuca ujemnego salda startowego)",
        lambda: bs.utworz_konto(N_OK_D, "Robert'); DROP TABLE-- <script>", -50),
    )
    N(
        "utworz_konto duplikat A",
        f"ValueError: Konto {N_OK_A} juz istnieje",
        lambda: bs.utworz_konto(N_OK_A, "Duplikat", 0),
        awaria=True,
        przyczyna="Zły komunikat",
        dotkliwosc="drobna",
    )
    N(
        "wplac(A, 0)",
        "ValueError: Kwota wplaty musi byc dodatnia",
        lambda: bs.wplac(N_OK_A, 0),
    )

    N(
        "wplac(A, -100)",
        "ValueError: Kwota wplaty musi byc dodatnia",
        lambda: bs.wplac(N_OK_A, -100),
    )
    N(
        "wplac(A, 'abc')",
        "TypeError: Kwota musi byc liczba",
        lambda: bs.wplac(N_OK_A, "abc"),
    )
    N(
        "wplac(A, '')",
        "TypeError: Kwota musi byc liczba",
        lambda: bs.wplac(N_OK_A, ""),
    )
    N(
        "wplac(A, 1e20)",
        "wplata przyjeta, saldo rosnie o bardzo duza kwote",
        lambda: bs.wplac(N_OK_A, 1e20),
    )
    N(
        "wplac(A, None)",
        "TypeError: Kwota musi byc liczba",
        lambda: bs.wplac(N_OK_A, None),
    )
    N(
        "wyplac(A, -1)",
        "ValueError: Kwota wyplaty musi byc dodatnia",
        lambda: bs.wyplac(N_OK_A, -1),
    )

    N(
        "wyplac(A, 5001) ponad limit dzienny",
        "ValueError: Przekroczono dzienny limit wyplat",
        lambda: bs.wyplac(N_OK_A, 5001),
    )
    N(
        "wyplac z konta, ktorego nie ma",
        "KontoNieIstnieje: Konto 9999999999 nie istnieje",
        lambda: bs.wyplac("9999999999", 10),
    )
    N(
        "zablokuj A i wyplac(A, 10)",
        f"KontoZablokowane: Konto {N_OK_A} jest zablokowane",
        lambda: _blokada_wyplata(bs),
    )
    N(
        "przelew(A do B, 50)",
        "przelew wykonany, saldo B rosnie o 50",
        lambda: bs.przelew(N_OK_A, N_OK_B, 50),
    )

    N(
        "przelew(A do B, -10)",
        "ValueError: Kwota przelewu musi byc dodatnia",
        lambda: bs.przelew(N_OK_A, N_OK_B, -10),
    )
    N(
        "przelew(A do konta, ktorego nie ma, 10)",
        "KontoNieIstnieje: Konto 9999999999 nie istnieje",
        lambda: bs.przelew(N_OK_A, "9999999999", 10),
        awaria=True,
        przyczyna="Zły wyjątek",
        dotkliwosc="poważna",
    )
    N(
        "przelew(A do B, 2000000) ponad limit 1000000",
        "ValueError: kwota ponad limit 1000000",
        lambda: bs.przelew(N_OK_A, N_OK_B, 2_000_000),
    )
    N(
        "nalicz_odsetki(B, -10%, 1 miesiac)",
        "odsetki policzone od ujemnej stopy, saldo B maleje",
        lambda: bs.nalicz_odsetki(N_OK_B, -10, 1),
    )

    N(
        "historia_w_okresie(A, dzis, dzis)",
        "wpisy z dzisiaj (przedzial domkniety)",
        lambda: bs.historia_w_okresie(N_OK_A, dzisiaj, dzisiaj),
        awaria=True,
        przyczyna="Zły wynik",
        dotkliwosc="poważna",
    )
    N(
        "przelew_zewnetrzny(B, 10), procesor zawsze niedostepny",
        "ProcesorNiedostepny, saldo B bez zmian",
        lambda: _zewnetrzny_pada(bs),
    )

    log_path = ROOT / "awarie.jsonl"
    log_linie = (
        log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    )
    api_linie = len((ROOT / "API.py").read_text(encoding="utf-8").splitlines())

    KOD.mkdir(parents=True, exist_ok=True)
    dane = {
        "linie": api_linie,
        "log_linii": len(log_linie),
        "wywolania": wyniki,
    }
    (KOD / "wywolania.json").write_text(
        json.dumps(dane, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n=== Koniec: wykonano {n} wywolan ===")


def _blokada_wyplata(bs):
    bs.zablokuj_konto(N_OK_A)
    try:
        return bs.wyplac(N_OK_A, 10)
    finally:
        bs.odblokuj_konto(N_OK_A)


def _zewnetrzny_pada(bs):
    saldo = bs.konta[N_OK_B].saldo
    try:
        bs.przelew_zewnetrzny(
            N_OK_B,
            "0000000000",
            10,
            procesor=ZewnetrznyProcesor(prawdopodobienstwo_awarii=1.0),
        )
    except Exception:
        if bs.konta[N_OK_B].saldo != saldo:
            raise AssertionError(f"saldo zmienione: {bs.konta[N_OK_B].saldo}")
        raise
    raise AssertionError("procesor nie zglosil awarii")


if __name__ == "__main__":
    main()
