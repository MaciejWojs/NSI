"""
Naiwne testy eksploracyjne SUT (blok P1).

Skrypt wywoluje publiczne operacje banku z danymi typowymi i nietypowymi,
zapisuje wynik kazdego wywolania i zostawia awarie w awarie.jsonl
(dekorator niezawodnosc_logger). Nie naprawia SUT.
"""

import json
import random
import threading
import time
import traceback
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import zespol_C as sut

LOG = Path("awarie.jsonl")
WYNIKI = Path("wyniki_testow.json")
wywolania = []
START = None


def wywolaj(opis, fn):
    """Jedno wywolanie z perspektywy uzytkownika (nie zagniezdzenie dekoratorow)."""
    t0 = time.time()
    try:
        wynik = fn()
        wpis = {
            "opis": opis,
            "status": "ok",
            "wynik": repr(wynik),
            "t_od_startu_s": round(t0 - START, 6),
        }
        print(f"OK   {opis} -> {wynik!r}")
    except Exception as e:
        wpis = {
            "opis": opis,
            "status": "wyjatek",
            "typ": type(e).__name__,
            "komunikat": str(e),
            "t_od_startu_s": round(t0 - START, 6),
        }
        print(f"EXC  {opis} -> {type(e).__name__}: {e}")
    wywolania.append(wpis)
    return wpis


def znajdz_numer(seed):
    """Proba w ciemno: 10 cyfr, az utworz_konto przestanie mowic o zlym numerze."""
    bank = sut.BankSystem()
    for i in range(1000):
        numer = f"{seed:06d}{i:04d}"
        try:
            bank.utworz_konto(numer, "szukanie")
            return numer
        except ValueError as e:
            if "Nieprawidlowy" not in str(e):
                return numer
        except Exception:
            return numer
    raise RuntimeError(f"nie udalo sie znalezc numeru dla seed={seed}")


def main():
    global START
    print("=== odkrywanie poprawnego numeru konta ===")
    n1 = znajdz_numer(100000)
    n2 = znajdz_numer(200000)
    n3 = znajdz_numer(300000)
    n4 = znajdz_numer(400000)
    n5 = znajdz_numer(500000)
    n6 = znajdz_numer(600000)
    n7 = znajdz_numer(700000)
    n8 = znajdz_numer(800000)
    print(f"numery: {n1}, {n2}, {n3}, {n4}, {n5}, {n6}, {n7}, {n8}")

    # Probne trafienia w zly numer nie naleza do sesji pomiarowej.
    if LOG.exists():
        LOG.unlink()
    START = time.time()

    bank = sut.BankSystem()

    print("\n=== sciezka podstawowa ===")
    wywolaj("utworz konto A", lambda: bank.utworz_konto(n1, "Anna Nowak", 1000))
    wywolaj("utworz konto B", lambda: bank.utworz_konto(n2, "Bartek Lis", 50))
    wywolaj("wplata 200", lambda: bank.wplac(n1, 200))
    wywolaj("wyplata 150", lambda: bank.wyplac(n1, 150))
    wywolaj("przelew A->B 100", lambda: bank.przelew(n1, n2, 100))
    wywolaj("odsetki 12% / 1 mies.", lambda: bank.nalicz_odsetki(n1, 12, 1))
    wywolaj(
        "historia wczoraj-jutro",
        lambda: bank.historia_w_okresie(n1, date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
    )
    wywolaj(
        "wyciag biezacy miesiac",
        lambda: bank.wyciag_miesieczny(n1, date.today().year, date.today().month),
    )
    wywolaj("zablokuj B", lambda: bank.zablokuj_konto(n2))
    wywolaj("odblokuj B", lambda: bank.odblokuj_konto(n2))

    print("\n=== dane nietypowe ===")
    wywolaj("numer pusty", lambda: bank.utworz_konto("", "X"))
    wywolaj("numer krotki", lambda: bank.utworz_konto("123", "X"))
    wywolaj("numer z literami", lambda: bank.utworz_konto("abcdefghij", "X"))
    wywolaj("numer ze znakami", lambda: bank.utworz_konto("12-34 56/7", "X"))
    wywolaj("numer za dlugi", lambda: bank.utworz_konto("12345678901", "X"))
    wywolaj("duplikat konta A", lambda: bank.utworz_konto(n1, "Ktos inny", 1))
    wywolaj("wplata ujemna", lambda: bank.wplac(n1, -10))
    wywolaj("wplata zero", lambda: bank.wplac(n1, 0))
    wywolaj("wplata napis", lambda: bank.wplac(n1, "100"))
    wywolaj("wplata None", lambda: bank.wplac(n1, None))
    wywolaj("wyplata wieksza niz saldo", lambda: bank.wyplac(n1, 10**9))
    wywolaj("wyplata zero", lambda: bank.wyplac(n1, 0))
    wywolaj("wyplata ujemna", lambda: bank.wyplac(n1, -5))
    wywolaj("wyplata napis", lambda: bank.wyplac(n1, "10"))
    wywolaj("konto nieistniejace", lambda: bank.wplac(n3, 10))
    wywolaj("przelew do nieistniejacego", lambda: bank.przelew(n1, n3, 10))
    wywolaj("przelew ujemny", lambda: bank.przelew(n1, n2, -1))
    wywolaj("przelew ponad milion", lambda: bank.przelew(n1, n2, 1_000_001))
    wywolaj("odsetki ujemna stopa", lambda: bank.nalicz_odsetki(n1, -1200, 1))
    wywolaj("odsetki ulamek miesiecy", lambda: bank.nalicz_odsetki(n1, 5, 1.5))
    wywolaj("odsetki ujemne miesiace", lambda: bank.nalicz_odsetki(n2, 12, -3))
    wywolaj("saldo poczatkowe ujemne", lambda: bank.utworz_konto(n3, "Cezary", -500))

    print("\n=== blokada i limit dzienny ===")
    bank2 = sut.BankSystem()
    wywolaj("utworz C", lambda: bank2.utworz_konto(n3, "Cezary", 20000))
    # n3 mogl juz powstac wyzej z ujemnym saldem na innym obiekcie bank; tu nowy BankSystem
    wywolaj("zablokuj C", lambda: bank2.zablokuj_konto(n3))
    wywolaj("wyplata na zablokowanym", lambda: bank2.wyplac(n3, 10))
    wywolaj("wplata na zablokowanym", lambda: bank2.wplac(n3, 10))
    wywolaj("odsetki na zablokowanym", lambda: bank2.nalicz_odsetki(n3, 12, 1))
    wywolaj("przelew z zablokowanego", lambda: bank2.przelew(n3, n3, 10))
    wywolaj("odblokuj C", lambda: bank2.odblokuj_konto(n3))
    wywolaj("wyplata 5000", lambda: bank2.wyplac(n3, 5000))
    wywolaj("wyplata ponad limit dzienny", lambda: bank2.wyplac(n3, 1))
    wywolaj("przelew 6000 (ponad limit wyplat)", lambda: bank2.przelew(n3, n3, 6000))

    print("\n=== historia i wyciag ===")
    konto = bank2._pobierz_konto(n3)
    konto.dodaj_wpis("wplata", Decimal("100.00"), date(2026, 1, 15))
    wywolaj(
        "historia granic wylacznie dzis",
        lambda: bank2.historia_w_okresie(n3, date.today(), date.today()),
    )
    wywolaj(
        "historia stycznia wlacznie",
        lambda: bank2.historia_w_okresie(n3, date(2026, 1, 15), date(2026, 1, 16)),
    )
    wywolaj(
        "historia stycznia dokladnie w dniu",
        lambda: bank2.historia_w_okresie(n3, date(2026, 1, 14), date(2026, 1, 15)),
    )
    wywolaj("wyciag stycznia", lambda: bank2.wyciag_miesieczny(n3, 2026, 1))
    saldo_po = bank2._pobierz_konto(n3).saldo
    print(f"INFO saldo C po wyciagu: {saldo_po}")

    print("\n=== wartosci specjalne na osobnym koncie ===")
    bank_z = sut.BankSystem()
    wywolaj("utworz konto zatrute", lambda: bank_z.utworz_konto(n6, "Zenon", 100))
    wywolaj("wplata True", lambda: bank_z.wplac(n6, True))
    wywolaj("wplata NaN", lambda: bank_z.wplac(n6, float("nan")))
    wywolaj("wplata +inf", lambda: bank_z.wplac(n6, float("inf")))
    print(f"INFO saldo zatrute: {bank_z._pobierz_konto(n6).saldo}")

    print("\n=== przelew zewnetrzny (kruchy procesor) ===")
    bank3 = sut.BankSystem()
    wywolaj("utworz D", lambda: bank3.utworz_konto(n4, "Daria", 500))
    pewny = sut.ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.0, generator=random.Random(1))
    wywolaj(
        "przelew zewn. procesor pewny",
        lambda: bank3.przelew_zewnetrzny(n4, "9999999999", 40, procesor=pewny),
    )
    zepsuty = sut.ZewnetrznyProcesor(prawdopodobienstwo_awarii=1.0, generator=random.Random(1))
    saldo_przed = bank3._pobierz_konto(n4).saldo
    wywolaj(
        "przelew zewn. procesor zawsze padnie",
        lambda: bank3.przelew_zewnetrzny(n4, "9999999999", 40, procesor=zepsuty),
    )
    saldo_po_awarii = bank3._pobierz_konto(n4).saldo
    print(f"INFO saldo przed/po awarii procesora: {saldo_przed} -> {saldo_po_awarii}")
    losowy = sut.ZewnetrznyProcesor(prawdopodobienstwo_awarii=0.3, generator=random.Random(7))
    for i in range(5):
        wywolaj(
            f"przelew zewn. losowy #{i + 1}",
            lambda p=losowy: bank3.przelew_zewnetrzny(n4, "9999999999", 1, procesor=p),
        )

    print("\n=== sondy potwierdzajace ===")
    bank5 = sut.BankSystem()
    wywolaj("utworz E na limit", lambda: bank5.utworz_konto(n7, "Ewa", 20000))
    wywolaj("utworz F", lambda: bank5.utworz_konto(n8, "Filip", 0))
    wywolaj("wyplata 5000 na E", lambda: bank5.wyplac(n7, 5000))
    wywolaj("przelew 100 po wyczerpaniu limitu", lambda: bank5.przelew(n7, n8, 100))
    print(f"INFO saldo E/F: {bank5.konta[n7].saldo} / {bank5.konta[n8].saldo}")

    bank6 = sut.BankSystem()
    wywolaj("utworz bogate", lambda: bank6.utworz_konto(n8, "Bogaty", 2_000_000))
    wywolaj("przelew ponad 1 mln", lambda: bank6.przelew(n8, n8, 1_000_001))
    wywolaj("odsetki -2400% / 1 mies.", lambda: bank6.nalicz_odsetki(n8, -2400, 1))
    print(f"INFO saldo po ujemnej stopie: {bank6.konta[n8].saldo}")
    bank6.konta[n8].dodaj_wpis("wplata", Decimal("100"), date(2026, 1, 15))
    wywolaj(
        "historia 14-16 stycznia",
        lambda: bank6.historia_w_okresie(n8, date(2026, 1, 14), date(2026, 1, 16)),
    )
    wywolaj(
        "historia 15-16 stycznia",
        lambda: bank6.historia_w_okresie(n8, date(2026, 1, 15), date(2026, 1, 16)),
    )

    print("\n=== wyscig wyplat (20 watkow po 100 przy saldzie 1000) ===")
    bank4 = sut.BankSystem()
    bank4.utworz_konto(n5, "Ewa", 1000)
    bariera = threading.Barrier(20)
    bledy_watkow = []

    def job():
        bariera.wait()
        try:
            bank4.wyplac(n5, 100)
        except Exception as e:
            bledy_watkow.append(type(e).__name__)

    watki = [threading.Thread(target=job) for _ in range(20)]
    for w in watki:
        w.start()
    for w in watki:
        w.join()
    saldo_race = bank4._pobierz_konto(n5).saldo
    historia_race = len(bank4._pobierz_konto(n5).historia)
    print(f"INFO saldo po wyscigu: {saldo_race}, wpisy historii: {historia_race}, wyjatki: {len(bledy_watkow)}")
    wywolania.append(
        {
            "opis": "wyscig 20x wyplata 100 przy saldzie 1000",
            "status": "ok" if saldo_race == 0 and historia_race == 10 else "wyjatek",
            "typ": "RaceCondition" if saldo_race != 0 or historia_race != 10 else None,
            "komunikat": f"saldo={saldo_race}, historia={historia_race}, odrzucone={len(bledy_watkow)}",
            "t_od_startu_s": round(time.time() - START, 6),
        }
    )

    print("\n=== log awarii ===")
    linie = []
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                linie.append(json.loads(line))
    print(f"wpisy w {LOG}: {len(linie)}")
    for wp in linie:
        print(
            f"  {wp['funkcja']:24} {wp['typ_bledu']:22} {wp['czas_do_awarii_s']:.6f}s  {wp['komunikat'][:80]}"
        )

    WYNIKI.write_text(
        json.dumps({"start": START, "wywolania": wywolania, "log": linie, "race": {
            "saldo": str(saldo_race),
            "historia": historia_race,
            "odrzucenia": len(bledy_watkow),
        }}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nzapisano {WYNIKI}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
