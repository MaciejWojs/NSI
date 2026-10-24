import json
from datetime import date
from decimal import Decimal

import pytest

from API import (
    BankSystem,
    KontoNieIstnieje,
    KontoZablokowane,
    ProcesorNiedostepny,
    ZewnetrznyProcesor,
    niezawodnosc_logger,
)


NR_1 = "1234567895"
NR_2 = "1111111119"
NR_3 = "1000000001"
NR_ZLY_CHECKSUM = "1234567896"


class ProcesorTestowy:
    def __init__(self, wynik=None, blad=None):
        self.wynik = wynik or {
            "status": "zaksiegowano",
            "numer_referencyjny": "REFSTUB",
        }
        self.blad = blad
        self.wywolania = []

    def wyslij_przelew(self, numer_konta_docelowego, kwota):
        self.wywolania.append((numer_konta_docelowego, kwota))
        if self.blad is not None:
            raise self.blad
        return self.wynik


@pytest.fixture(scope="function")
def setup_module():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", 1000)
    bs.utworz_konto(NR_2, "Johnathan Johnson", 7000)
    yield {
        "nr_konta1": NR_1,
        "nr_konta2": NR_2,
        "bs": bs,
    }


def test_BankSystem(setup_module):
    bs = setup_module["bs"]

    assert isinstance(bs, BankSystem)
    assert bs.konta.keys() == {NR_1, NR_2}
    assert bs.konta[NR_1].saldo == Decimal("1000")
    assert bs.konta[NR_2].saldo == Decimal("7000")


def test_BankSystem_utworz_konto(setup_module):
    bs = setup_module["bs"]
    numer = setup_module["nr_konta1"]

    with pytest.raises(ValueError) as zly_numer:
        bs.utworz_konto(NR_ZLY_CHECKSUM, "John Doe", 1000)
    assert str(zly_numer.value) == "Nieprawidlowy numer konta"

    with pytest.raises(ValueError) as duplikat:
        bs.utworz_konto(numer, "Ktos inny", 50)
    assert str(duplikat.value) == "Konto {numer} juz istnieje"
    assert bs.konta[numer].wlasciciel == "John Doe"
    assert bs.konta[numer].saldo == Decimal("1000")
    assert len(bs.konta) == 2


def test_BankSystem_utworz_konto_sukces():
    bs = BankSystem()

    konto = bs.utworz_konto(NR_3, "Anna Nowak", Decimal("15.50"))

    assert konto is bs.konta[NR_3]
    assert konto.numer == NR_3
    assert konto.wlasciciel == "Anna Nowak"
    assert konto.saldo == Decimal("15.50")
    assert konto.historia == []
    assert konto.status == "aktywne"


def test_numer_poprawny(setup_module):
    bs = setup_module["bs"]

    assert bs._numer_poprawny(NR_1) is True
    assert bs._numer_poprawny(NR_ZLY_CHECKSUM) is False
    assert bs._numer_poprawny(1234567895) is False
    assert bs._numer_poprawny("1234") is False
    assert bs._numer_poprawny("abcdefghij") is False


def test_BankSystem_pobierz_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]

    konto = bs._pobierz_konto(nr1)

    assert konto is bs.konta[nr1]
    assert konto.numer == nr1
    assert konto.saldo == Decimal("1000")

    with pytest.raises(KontoNieIstnieje) as brak:
        bs._pobierz_konto(NR_ZLY_CHECKSUM)
    assert str(brak.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"
    assert NR_ZLY_CHECKSUM not in bs.konta


def test_BankSystem_zablokuj_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]

    bs.zablokuj_konto(nr1)

    assert bs.konta[nr1].status == "zablokowane"
    assert bs.konta[nr1].saldo == Decimal("1000")
    assert bs.konta[setup_module["nr_konta2"]].status == "aktywne"


def test_BankSystem_odblokuj_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    bs.zablokuj_konto(nr1)

    bs.odblokuj_konto(nr1)

    assert bs.konta[nr1].status == "aktywne"
    assert bs.konta[nr1].saldo == Decimal("1000")


def test_BankSystem_zablokuj_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.zablokuj_konto(NR_ZLY_CHECKSUM)
    assert str(blad.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"
    assert all(konto.status == "aktywne" for konto in bs.konta.values())


def test_BankSystem_odblokuj_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.odblokuj_konto(NR_ZLY_CHECKSUM)
    assert str(blad.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"


def test_BankSystem_pobierz_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as blad:
        bs._pobierz_konto(NR_ZLY_CHECKSUM)
    assert str(blad.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"


def test_BankSystem_wplac(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    dzisiaj = date.today()

    saldo = bs.wplac(nr1, 200)

    assert saldo == Decimal("1200")
    assert bs.konta[nr1].saldo == Decimal("1200")
    assert bs.konta[nr1].historia == [(dzisiaj, "wplata", Decimal("200"))]
    assert bs.konta[setup_module["nr_konta2"]].saldo == Decimal("7000")


def test_BankSystem_wplac_bledy(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]

    with pytest.raises(TypeError) as typ:
        bs.wplac(nr1, "100")
    assert str(typ.value) == "Kwota musi byc liczba"

    with pytest.raises(ValueError) as zero:
        bs.wplac(nr1, 0)
    assert str(zero.value) == "Kwota wplaty musi byc dodatnia"

    with pytest.raises(ValueError) as ujemna:
        bs.wplac(nr1, Decimal("-0.01"))
    assert str(ujemna.value) == "Kwota wplaty musi byc dodatnia"

    assert bs.konta[nr1].saldo == Decimal("1000")
    assert bs.konta[nr1].historia == []


def test_BankSystem_wplac_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.wplac(NR_ZLY_CHECKSUM, 100)
    assert str(blad.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"
    assert bs.konta[NR_1].saldo == Decimal("1000")


def test_BankSystem_wyplac(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    nr2 = setup_module["nr_konta2"]
    dzisiaj = date.today()

    saldo = bs.wyplac(nr1, 100)

    assert saldo == Decimal("900")
    assert bs.konta[nr1].saldo == Decimal("900")
    assert bs.konta[nr1].historia == [(dzisiaj, "wyplata", Decimal("100"))]
    assert bs.konta[nr1].status == "aktywne"

    bs.zablokuj_konto(nr1)
    with pytest.raises(KontoZablokowane) as blokada:
        bs.wyplac(nr1, 100)
    assert str(blokada.value) == f"Konto {nr1} jest zablokowane"
    assert bs.konta[nr1].saldo == Decimal("900")
    assert bs.konta[nr1].historia == [(dzisiaj, "wyplata", Decimal("100"))]
    bs.odblokuj_konto(nr1)
    assert bs.konta[nr1].status == "aktywne"

    with pytest.raises(ValueError) as ujemna:
        bs.wyplac(nr2, -100)
    assert str(ujemna.value) == "Kwota wyplaty musi byc dodatnia"

    with pytest.raises(ValueError) as zero:
        bs.wyplac(nr2, 0)
    assert str(zero.value) == "Kwota wyplaty musi byc dodatnia"

    with pytest.raises(ValueError) as brak_srodkow:
        bs.wyplac(nr2, 10000)
    assert str(brak_srodkow.value) == "Niewystarczajace srodki na koncie"

    with pytest.raises(ValueError) as limit:
        bs.wyplac(nr2, 6500)
    assert str(limit.value) == "Przekroczono dzienny limit wyplat"

    assert bs.konta[nr2].saldo == Decimal("7000")
    assert bs.konta[nr2].historia == []


def test_BankSystem_wyplac_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.wyplac(NR_ZLY_CHECKSUM, 100)
    assert str(blad.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"


def test_BankSystem_przelew(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    nr2 = setup_module["nr_konta2"]
    dzisiaj = date.today()

    saldo = bs.przelew(nr1, nr2, 100)

    assert saldo == Decimal("900")
    assert bs.konta[nr1].saldo == Decimal("900")
    assert bs.konta[nr2].saldo == Decimal("7100")
    assert bs.konta[nr1].historia == [
        (dzisiaj, "przelew_wychodzacy", Decimal("100"))
    ]
    assert bs.konta[nr2].historia == [
        (dzisiaj, "przelew_przychodzacy", Decimal("100"))
    ]
    assert bs.konta[nr1].status == "aktywne"
    assert bs.konta[nr2].status == "aktywne"


def test_BankSystem_przelew_bledy(setup_module):
    bs = setup_module["bs"]
    saldo_1 = bs.konta[NR_1].saldo
    saldo_2 = bs.konta[NR_2].saldo

    bs.zablokuj_konto(NR_1)
    with pytest.raises(KontoZablokowane) as blokada:
        bs.przelew(NR_1, NR_2, 10)
    assert str(blokada.value) == "Konto {numer_z} jest zablokowane"
    bs.odblokuj_konto(NR_1)

    with pytest.raises(ValueError) as ujemna:
        bs.przelew(NR_1, NR_2, -1)
    assert str(ujemna.value) == "Kwota przelewu musi byc dodatnia"

    with pytest.raises(ValueError) as zero:
        bs.przelew(NR_1, NR_2, 0)
    assert str(zero.value) == "Kwota przelewu musi byc dodatnia"

    with pytest.raises(ValueError) as brak:
        bs.przelew(NR_1, NR_2, Decimal("1000.01"))
    assert str(brak.value) == "Niewystarczajace srodki na koncie zrodlowym"

    assert bs.konta[NR_1].saldo == saldo_1
    assert bs.konta[NR_2].saldo == saldo_2
    assert bs.konta[NR_1].historia == []
    assert bs.konta[NR_2].historia == []


def test_BankSystem_przelew_limit_systemowy(setup_module):
    bs = setup_module["bs"]
    bs.utworz_konto(NR_3, "Anna Nowak", Decimal("3000000"))

    with pytest.raises(ValueError) as limit:
        bs.przelew(NR_3, NR_1, Decimal("2000000"))
    assert str(limit.value) == "Przelew przekracza dzienny limit systemowy"
    assert bs.konta[NR_3].saldo == Decimal("3000000")
    assert bs.konta[NR_1].saldo == Decimal("1000")
    assert bs.konta[NR_3].historia == []


def test_BankSystem_przelew_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]

    with pytest.raises(KontoNieIstnieje) as zrodlo:
        bs.przelew(NR_ZLY_CHECKSUM, NR_2, 100)
    assert str(zrodlo.value) == f"Konto {NR_ZLY_CHECKSUM} nie istnieje"
    assert bs.konta[NR_2].saldo == Decimal("7000")
    assert bs.konta[NR_2].historia == []

    with pytest.raises(KeyError):
        bs.przelew(NR_1, NR_3, 100)
    assert bs.konta[NR_1].saldo == Decimal("1000")
    assert bs.konta[NR_1].historia == []


def test_BankSystem_nalicz_odsetki_zaokraglenie(setup_module):
    bs = setup_module["bs"]
    bs.utworz_konto(NR_3, "Anna Nowak", Decimal("1"))
    dzisiaj = date.today()

    saldo = bs.nalicz_odsetki(NR_3, 6, 1)

    assert saldo == Decimal("1.01")
    assert bs.konta[NR_3].saldo == Decimal("1.01")
    assert bs.konta[NR_3].historia == [
        (dzisiaj, "odsetki", Decimal("0.01"))
    ]


def test_BankSystem_nalicz_odsetki_zero_miesiecy_i_brak_konta(setup_module):
    bs = setup_module["bs"]

    saldo = bs.nalicz_odsetki(NR_1, 10, 0)

    assert saldo == Decimal("1000")
    assert bs.konta[NR_1].historia == []

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.nalicz_odsetki(NR_3, 5, 1)
    assert str(blad.value) == f"Konto {NR_3} nie istnieje"


def test_BankSystem_historia_w_okresie(setup_module):
    bs = setup_module["bs"]
    konto = bs.konta[NR_1]
    wewnatrz = (date(2024, 1, 15), "wplata", Decimal("10.00"))
    konto.dodaj_wpis("wyplata", Decimal("1.00"), date(2023, 12, 31))
    konto.dodaj_wpis("wplata", Decimal("2.00"), date(2024, 1, 1))
    konto.dodaj_wpis(*wewnatrz[1:], wewnatrz[0])
    konto.dodaj_wpis("wyplata", Decimal("3.00"), date(2024, 1, 31))
    konto.dodaj_wpis("wplata", Decimal("4.00"), date(2024, 2, 1))

    wynik = bs.historia_w_okresie(NR_1, date(2024, 1, 1), date(2024, 1, 31))

    assert wynik == [wewnatrz]
    assert bs.historia_w_okresie(NR_1, date(2025, 1, 1), date(2025, 2, 1)) == []

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.historia_w_okresie(NR_3, date(2024, 1, 1), date(2024, 2, 1))
    assert str(blad.value) == f"Konto {NR_3} nie istnieje"


def test_BankSystem_wyciag_miesieczny(setup_module):
    bs = setup_module["bs"]
    konto = bs.utworz_konto(NR_3, "Anna Nowak", Decimal("123.45"))
    konto.dodaj_wpis("wplata", Decimal("10.00"), date(2024, 5, 1))
    konto.dodaj_wpis("przelew_przychodzacy", Decimal("2.50"), date(2024, 5, 15))
    konto.dodaj_wpis("odsetki", Decimal("0.01"), date(2024, 5, 31))
    konto.dodaj_wpis("wyplata", Decimal("3.00"), date(2024, 5, 10))
    konto.dodaj_wpis("przelew_wychodzacy", Decimal("1.25"), date(2024, 5, 20))
    konto.dodaj_wpis("przelew_zewnetrzny", Decimal("99.00"), date(2024, 5, 21))
    konto.dodaj_wpis("wplata", Decimal("100.00"), date(2024, 6, 1))
    konto.dodaj_wpis("wyplata", Decimal("50.00"), date(2023, 5, 1))

    wyciag = bs.wyciag_miesieczny(NR_3, 2024, 5)

    assert wyciag == {
        "wplaty": Decimal("12.51"),
        "wyplaty": Decimal("4.25"),
        "saldo_koncowe": Decimal("123.45"),
    }

    pusty = bs.wyciag_miesieczny(NR_1, 1999, 1)
    assert pusty == {
        "wplaty": Decimal("0"),
        "wyplaty": Decimal("0"),
        "saldo_koncowe": Decimal("1000"),
    }

    with pytest.raises(KontoNieIstnieje) as blad:
        bs.wyciag_miesieczny("0000000000", 2024, 5)
    assert str(blad.value) == "Konto 0000000000 nie istnieje"


def test_BankSystem_przelew_zewnetrzny_z_procesorem(setup_module):
    bs = setup_module["bs"]
    procesor = ProcesorTestowy()
    dzisiaj = date.today()

    wynik = bs.przelew_zewnetrzny(
        NR_1, "9988776655", Decimal("150.50"), procesor=procesor
    )

    assert wynik == {
        "status": "zaksiegowano",
        "numer_referencyjny": "REFSTUB",
    }
    assert procesor.wywolania == [("9988776655", Decimal("150.50"))]
    assert bs.konta[NR_1].saldo == Decimal("849.50")
    assert bs.konta[NR_1].historia == [
        (dzisiaj, "przelew_zewnetrzny", Decimal("150.50"))
    ]
    assert bs.konta[NR_2].saldo == Decimal("7000")
    assert bs.konta[NR_2].historia == []


def test_BankSystem_przelew_zewnetrzny_cale_saldo_i_awaria_procesora(setup_module):
    bs = setup_module["bs"]
    procesor = ProcesorTestowy(
        blad=ProcesorNiedostepny("Zewnetrzny procesor platnosci nie odpowiada")
    )

    with pytest.raises(ProcesorNiedostepny) as blad:
        bs.przelew_zewnetrzny(NR_1, "9988776655", Decimal("1000"), procesor)
    assert str(blad.value) == "Zewnetrzny procesor platnosci nie odpowiada"
    assert procesor.wywolania == [("9988776655", Decimal("1000"))]
    assert bs.konta[NR_1].saldo == Decimal("1000")
    assert bs.konta[NR_1].historia == []

    sprawny = ZewnetrznyProcesor(prawdopodobienstwo_awarii=0)
    wynik = bs.przelew_zewnetrzny(NR_1, "9988776655", Decimal("1000"), sprawny)

    assert wynik["status"] == "zaksiegowano"
    assert sprawny.licznik_wywolan == 1
    assert bs.konta[NR_1].saldo == Decimal("0")


def test_BankSystem_przelew_zewnetrzny_bledy_przed_procesorem(setup_module):
    bs = setup_module["bs"]
    procesor = ProcesorTestowy()

    bs.zablokuj_konto(NR_1)
    with pytest.raises(KontoZablokowane) as blokada:
        bs.przelew_zewnetrzny(NR_1, "9988776655", 10, procesor)
    assert str(blokada.value) == f"Konto {NR_1} jest zablokowane"
    bs.odblokuj_konto(NR_1)

    with pytest.raises(ValueError) as ujemna:
        bs.przelew_zewnetrzny(NR_1, "9988776655", Decimal("-1"), procesor)
    assert str(ujemna.value) == "Kwota przelewu musi byc dodatnia"

    with pytest.raises(ValueError) as zero:
        bs.przelew_zewnetrzny(NR_1, "9988776655", 0, procesor)
    assert str(zero.value) == "Kwota przelewu musi byc dodatnia"

    with pytest.raises(ValueError) as brak:
        bs.przelew_zewnetrzny(NR_1, "9988776655", Decimal("1000.01"), procesor)
    assert str(brak.value) == "Niewystarczajace srodki na koncie zrodlowym"

    with pytest.raises(KontoNieIstnieje) as nie_ma:
        bs.przelew_zewnetrzny(NR_3, "9988776655", 10, procesor)
    assert str(nie_ma.value) == f"Konto {NR_3} nie istnieje"

    assert procesor.wywolania == []
    assert bs.konta[NR_1].saldo == Decimal("1000")
    assert bs.konta[NR_1].historia == []
    assert bs.konta[NR_1].status == "aktywne"


def test_ZewnetrznyProcesor_awaria_i_sukces():
    pewny = ZewnetrznyProcesor(prawdopodobienstwo_awarii=0)
    wynik = pewny.wyslij_przelew("9988776655", Decimal("1.00"))
    assert wynik["status"] == "zaksiegowano"
    assert wynik["numer_referencyjny"] == "REF000001"
    assert pewny.licznik_wywolan == 1

    awaryjny = ZewnetrznyProcesor(prawdopodobienstwo_awarii=1)
    with pytest.raises(ProcesorNiedostepny, match="nie odpowiada"):
        awaryjny.wyslij_przelew("9988776655", Decimal("1.00"))
    assert awaryjny.licznik_wywolan == 1


def test_niezawodnosc_logger_zapisuje_blad_do_jsonl(tmp_path):
    log_path = tmp_path / "awarie.jsonl"

    @niezawodnosc_logger(log_path=str(log_path))
    def awaryjna(x, y=1):
        raise RuntimeError(f"awaria {x}")

    @niezawodnosc_logger(log_path=str(log_path))
    def sprawna(x):
        return x + 1

    assert sprawna(1) == 2
    assert sprawna.__name__ == "sprawna"
    assert not log_path.exists()

    with pytest.raises(RuntimeError, match="awaria 7"):
        awaryjna(7, y=3)

    wpis = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert wpis["funkcja"] == "awaryjna"
    assert wpis["args"] == "(7,)"
    assert wpis["kwargs"] == "{'y': 3}"
    assert wpis["typ_bledu"] == "RuntimeError"
    assert wpis["komunikat"] == "awaria 7"
    assert wpis["czas_do_awarii_s"] >= 0
