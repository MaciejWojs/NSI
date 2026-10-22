from datetime import date
from decimal import Decimal

import pytest

from API import Konto


NR_KONTA = "1234567895"


@pytest.fixture(scope="function")
def setup_module():
    konto = Konto(NR_KONTA, "John Doe", 1000)
    yield {"konto": konto}


def test_Konto_inicjalizacja(setup_module):
    konto = setup_module["konto"]

    assert konto.numer == NR_KONTA
    assert konto.wlasciciel == "John Doe"
    assert type(konto.saldo) is Decimal
    assert konto.saldo == Decimal("1000")
    assert konto.historia == []
    assert konto.status == "aktywne"


def test_Konto_saldo_poczatkowe_domyslne():
    konto = Konto(NR_KONTA, "John Doe")

    assert type(konto.saldo) is Decimal
    assert konto.saldo == Decimal("0")
    assert konto.historia == []
    assert konto.status == "aktywne"


def test_Konto_dodaj_wpis_z_data(setup_module):
    konto = setup_module["konto"]
    dzien = date(2024, 6, 1)

    konto.dodaj_wpis("wplata", Decimal("1000.00"), dzien)

    assert konto.historia == [(dzien, "wplata", Decimal("1000.00"))]
    assert konto.saldo == Decimal("1000")
    assert konto.status == "aktywne"


def test_Konto_dodaj_wpis(setup_module):
    konto = setup_module["konto"]
    dzisiaj = date.today()

    konto.dodaj_wpis("wplata", 1000)

    assert konto.historia == [(dzisiaj, "wplata", 1000)]
    assert len(konto.historia) == 1


def test_Konto_dodaj_wpis_dokleja_kolejne_operacje(setup_module):
    konto = setup_module["konto"]
    wczesniej = date(2024, 1, 2)
    dzisiaj = date.today()

    konto.dodaj_wpis("wplata", Decimal("10.00"), wczesniej)
    konto.dodaj_wpis("wyplata", Decimal("4.50"))

    assert konto.historia == [
        (wczesniej, "wplata", Decimal("10.00")),
        (dzisiaj, "wyplata", Decimal("4.50")),
    ]
