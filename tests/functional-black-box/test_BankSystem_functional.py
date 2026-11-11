from datetime import date
from decimal import Decimal

import pytest

from API import (
    BankSystem,
    Konto,
    KontoNieIstnieje,
    KontoZablokowane,
)

NR_1 = "1234567895"
NR_2 = "1111111119"
NR_3 = "1000000001"
NR_ZLY_CHECKSUM = "1234567896"
NR_ZA_KROTKI = "123456789"
NR_ZA_DLUGI = "12345678967"
NR_NIELICZBOWY = "123456789a"


def test_BankSystem_utworz_konto():
    # Poprawny numer: 10 cyfr i zgodna cyfra kontrolna
    bs = BankSystem()
    wynik = bs.utworz_konto(NR_1, "John Doe")
    assert isinstance(wynik, Konto)
    assert wynik.numer == NR_1
    assert wynik.saldo == Decimal(0)
    assert wynik.status == "aktywne"
    assert wynik.historia == []

    # Numer juz zajety
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_1, "John Doe")

    # Zla cyfra kontrolna
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_ZLY_CHECKSUM, "John Doe")

    # Dlugosc 9 i 11: granice poprawnej dlugosci 10
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_ZA_KROTKI, "John Doe")
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_ZA_DLUGI, "John Doe")

    # Znaki inne niz cyfry oraz numer, ktory nie jest napisem
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_NIELICZBOWY, "John Doe")
    with pytest.raises(ValueError):
        bs.utworz_konto(1234567895, "John Doe")

    assert list(bs.konta) == [NR_1]


def test_BankSystem_blokady_i_odblokowania():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe")

    bs.zablokuj_konto(NR_1)
    assert bs.konta[NR_1].status == "zablokowane"

    bs.odblokuj_konto(NR_1)
    assert bs.konta[NR_1].status == "aktywne"

    with pytest.raises(KontoNieIstnieje):
        bs.zablokuj_konto(NR_2)

    with pytest.raises(KontoNieIstnieje):
        bs.odblokuj_konto(NR_2)


def test_BankSystem_wplac():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe")

    # Klasy kwoty dodatniej: int, float, Decimal oraz grosz nad zerem
    assert bs.wplac(NR_1, 100) == Decimal(100)
    assert bs.wplac(NR_1, 10.5) == Decimal("110.5")
    assert bs.wplac(NR_1, Decimal("0.01")) == Decimal("110.51")

    # Blokada nie dotyczy wplaty
    bs.zablokuj_konto(NR_1)
    assert bs.wplac(NR_1, 1) == Decimal("111.51")
    assert bs.konta[NR_1].status == "zablokowane"

    # Napis, takze liczbowy, nie jest int, float ani Decimal
    with pytest.raises(TypeError):
        bs.wplac(NR_1, "abc")
    with pytest.raises(TypeError):
        bs.wplac(NR_1, "100")

    # Zero i wartosci ujemne, w tym tuż pod zerem
    with pytest.raises(ValueError):
        bs.wplac(NR_1, -100)
    with pytest.raises(ValueError):
        bs.wplac(NR_1, Decimal("-0.01"))
    with pytest.raises(ValueError):
        bs.wplac(NR_1, 0)

    assert bs.konta[NR_1].saldo == Decimal("111.51")

    with pytest.raises(KontoNieIstnieje):
        bs.wplac(NR_2, 100)


def test_BankSystem_wyplac_tablica_decyzyjna():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))
    bs.utworz_konto(NR_2, "Jane Doe", saldo_poczatkowe=Decimal(6000))

    # Konto nie istnieje
    with pytest.raises(KontoNieIstnieje):
        bs.wyplac(NR_3, Decimal(10))

    # Blokada przesadza wynik, takze przy kwocie ujemnej
    bs.zablokuj_konto(NR_1)
    with pytest.raises(KontoZablokowane):
        bs.wyplac(NR_1, Decimal(10))
    with pytest.raises(KontoZablokowane):
        bs.wyplac(NR_1, Decimal(-10))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_1].historia == []
    bs.odblokuj_konto(NR_1)

    # Kwota niedodatnia
    with pytest.raises(ValueError):
        bs.wyplac(NR_1, Decimal(-1))
    with pytest.raises(ValueError):
        bs.wyplac(NR_1, Decimal("-0.01"))
    with pytest.raises(ValueError):
        bs.wyplac(NR_1, 0)

    # Powyżej salda, nadal poniżej limitu dziennego
    with pytest.raises(ValueError):
        bs.wyplac(NR_1, Decimal("100.01"))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_1].historia == []

    # Granica salda: kwota równa saldu
    assert bs.wyplac(NR_1, Decimal(100)) == Decimal(0)
    assert bs.konta[NR_1].saldo == Decimal(0)

    # Najmniejsza kwota dodatnia
    bs.wplac(NR_1, Decimal("0.01"))
    assert bs.wyplac(NR_1, Decimal("0.01")) == Decimal(0)

    # Granica limitu dziennego 5000 przy saldzie 6000
    assert bs.wyplac(NR_2, Decimal(5000)) == Decimal(1000)
    assert bs.konta[NR_2].saldo == Decimal(1000)

    bs.utworz_konto(NR_3, "Ann", saldo_poczatkowe=Decimal(6000))
    with pytest.raises(ValueError):
        bs.wyplac(NR_3, Decimal("5000.01"))
    assert bs.konta[NR_3].saldo == Decimal(6000)
    assert bs.konta[NR_3].historia == []


def test_BankSystem_wyplac_limit_z_przelewem():
    # Limit dzienny liczy wypłaty i przelewy wychodzące z tego samego dnia
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(6000))
    bs.utworz_konto(NR_2, "Jane Doe")

    bs.przelew(NR_1, NR_2, Decimal(3000))
    assert bs.wyplac(NR_1, Decimal(2000)) == Decimal(1000)

    with pytest.raises(ValueError):
        bs.wyplac(NR_1, Decimal("0.01"))
    assert bs.konta[NR_1].saldo == Decimal(1000)


@pytest.mark.xfail(
    reason=(
        "Dokumentacja wymaga TypeError, gdy kwota nie jest liczba. "
        "wyplac przekazuje napis do Decimal i zgłasza InvalidOperation."
    ),
    strict=False,
)
def test_BankSystem_wyplac_napis_nieliczbowy():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))

    with pytest.raises(TypeError):
        bs.wyplac(NR_1, "abc")
    assert bs.konta[NR_1].saldo == Decimal(100)


@pytest.mark.xfail(
    reason=(
        "Napis '100' nie jest int, float ani Decimal. "
        "wyplac księguje go zamiast zgłosić TypeError."
    ),
    strict=False,
)
def test_BankSystem_wyplac_napis_liczbowy():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))

    with pytest.raises(TypeError):
        bs.wyplac(NR_1, "100")
    assert bs.konta[NR_1].saldo == Decimal(100)


def test_BankSystem_przelew_tablica_decyzyjna():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))
    bs.utworz_konto(NR_2, "Jane Doe", saldo_poczatkowe=Decimal(50))

    # Brak konta źródłowego
    with pytest.raises(KontoNieIstnieje):
        bs.przelew(NR_3, NR_1, Decimal(10))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_1].historia == []

    # Blokada źródła
    bs.zablokuj_konto(NR_1)
    with pytest.raises(KontoZablokowane):
        bs.przelew(NR_1, NR_2, Decimal(10))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_2].saldo == Decimal(50)
    bs.odblokuj_konto(NR_1)

    # Kwota niedodatnia
    with pytest.raises(ValueError):
        bs.przelew(NR_1, NR_2, 0)
    with pytest.raises(ValueError):
        bs.przelew(NR_1, NR_2, Decimal("-0.01"))

    # Powyżej salda źródła
    with pytest.raises(ValueError):
        bs.przelew(NR_1, NR_2, Decimal("100.01"))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_2].saldo == Decimal(50)
    assert bs.konta[NR_1].historia == []

    # Granica salda: przelew na całe saldo
    assert bs.przelew(NR_1, NR_2, Decimal(100)) == Decimal(0)
    assert bs.konta[NR_2].saldo == Decimal(150)

    # Cel zablokowany nie jest w specyfikacji powodem odmowy
    bs.wplac(NR_1, Decimal(20))
    bs.zablokuj_konto(NR_2)
    assert bs.przelew(NR_1, NR_2, Decimal(20)) == Decimal(0)
    assert bs.konta[NR_2].saldo == Decimal(170)
    assert bs.konta[NR_2].status == "zablokowane"


def test_BankSystem_przelew_granica_limitu():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(1000000))
    bs.utworz_konto(NR_2, "Jane Doe")

    assert bs.przelew(NR_1, NR_2, Decimal(1000000)) == Decimal(0)
    assert bs.konta[NR_2].saldo == Decimal(1000000)

    bs.utworz_konto(NR_3, "Ann", saldo_poczatkowe=Decimal("1000000.01"))
    with pytest.raises(ValueError):
        bs.przelew(NR_3, NR_2, Decimal("1000000.01"))
    assert bs.konta[NR_3].saldo == Decimal("1000000.01")
    assert bs.konta[NR_2].saldo == Decimal(1000000)


@pytest.mark.xfail(
    reason=(
        "Dokumentacja wymaga KontoNieIstnieje, gdy konto docelowe nie istnieje. "
        "Implementacja czyta self.konta[numer_do] i zgłasza KeyError."
    ),
    strict=False,
)
def test_BankSystem_przelew_konto_docelowe_nie_istnieje():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))

    with pytest.raises(KontoNieIstnieje):
        bs.przelew(NR_1, NR_2, Decimal(10))
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_1].historia == []


@pytest.mark.xfail(
    reason=(
        "Dokumentacja wymaga TypeError, gdy kwota nie jest liczba. "
        "przelew przekazuje napis do Decimal i zgłasza InvalidOperation."
    ),
    strict=False,
)
def test_BankSystem_przelew_napis_nieliczbowy():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))
    bs.utworz_konto(NR_2, "Jane Doe")

    with pytest.raises(TypeError):
        bs.przelew(NR_1, NR_2, "abc")
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_2].saldo == Decimal(0)


@pytest.mark.xfail(
    reason=(
        "Napis '100' nie jest int, float ani Decimal. "
        "przelew księguje go zamiast zgłosić TypeError."
    ),
    strict=False,
)
def test_BankSystem_przelew_napis_liczbowy():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe", saldo_poczatkowe=Decimal(100))
    bs.utworz_konto(NR_2, "Jane Doe")

    with pytest.raises(TypeError):
        bs.przelew(NR_1, NR_2, "100")
    assert bs.konta[NR_1].saldo == Decimal(100)
    assert bs.konta[NR_2].saldo == Decimal(0)


def test_BankSystem_historia_w_okresie_brak_konta():
    bs = BankSystem()

    with pytest.raises(KontoNieIstnieje):
        bs.historia_w_okresie(NR_1, date(2024, 1, 1), date(2024, 1, 31))


@pytest.mark.xfail(
    reason=(
        "Dokumentacja wymaga przedziału domkniętego, łącznie z datami od i do. "
        "Implementacja zostawia tylko daty spomiędzy granic."
    ),
    strict=False,
)
def test_BankSystem_historia_w_okresie_granice_wlacznie():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe")
    konto = bs.konta[NR_1]
    od = date(2024, 1, 1)
    do = date(2024, 1, 31)
    konto.dodaj_wpis("wyplata", Decimal("1.00"), date(2023, 12, 31))
    konto.dodaj_wpis("wplata", Decimal("2.00"), od)
    konto.dodaj_wpis("wplata", Decimal("10.00"), date(2024, 1, 15))
    konto.dodaj_wpis("wyplata", Decimal("3.00"), do)
    konto.dodaj_wpis("wplata", Decimal("4.00"), date(2024, 2, 1))

    wynik = bs.historia_w_okresie(NR_1, od, do)

    assert wynik == [
        (od, "wplata", Decimal("2.00")),
        (date(2024, 1, 15), "wplata", Decimal("10.00")),
        (do, "wyplata", Decimal("3.00")),
    ]
