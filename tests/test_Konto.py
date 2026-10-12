from datetime import date

import pytest

from API import Konto


@pytest.fixture(scope="module")
def setup_module():
    numer_konta_pierwszego = "1234567895"
    konto = Konto(numer_konta_pierwszego, "John Doe", 1000)
    yield {
        "konto": konto,
    }
    print("Testy zakończone")


def test_Konto_dodaj_wpis(setup_module):
    konto = setup_module["konto"]
    konto.dodaj_wpis("wplata", 1000)
    assert konto.historia == [(date.today(), "wplata", 1000)]
