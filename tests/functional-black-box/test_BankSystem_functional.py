
from decimal import Decimal

import pytest

from API import (
    BankSystem,
    Konto,
    KontoNieIstnieje,
)

NR_1 = "1234567895"
NR_2 = "1111111119"
NR_3 = "1000000001"
NR_ZLY_CHECKSUM = "1234567896"
NR_ZA_KROTKI = "123456789"
NR_ZA_DLUGI = "12345678967"


def test_BankSystem_utworz_konto():
    # Poprawne konto
    bs = BankSystem()
    wynik = bs.utworz_konto(NR_1, "John Doe")
    assert wynik is not None
    assert isinstance(wynik, Konto)

    # Konto juz istnieje
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_1, "John Doe")

    # Konto z niepoprawnym sumarycznym kontrolnym bitem
    with pytest.raises(ValueError):
        bs.utworz_konto(NR_ZLY_CHECKSUM, "John Doe")


def test_BankSystem_blokady_i_odblokowania():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe")

    # Blokowanie kont
    bs.zablokuj_konto(NR_1)
    assert bs._pobierz_konto(NR_1).status == "zablokowane"

    # Odblokowanie kont
    bs.odblokuj_konto(NR_1)
    assert bs._pobierz_konto(NR_1).status == "aktywne"

    # Blokowanie nieistniejacego konta
    with pytest.raises(KontoNieIstnieje):
        bs.zablokuj_konto(NR_2)

    # Odblokowanie nieistniejacego konta
    with pytest.raises(KontoNieIstnieje):
        bs.odblokuj_konto(NR_2)


def test_BankSystem_wplac():
    bs = BankSystem()
    bs.utworz_konto(NR_1, "John Doe")

    # Wplata na konto
    assert bs.wplac(NR_1, 100) == Decimal(100)

    # Kwota nie jest liczba
    with pytest.raises(TypeError):
        bs.wplac(NR_1, "abc")

    # Kwota jest ujemna
    with pytest.raises(ValueError):
        bs.wplac(NR_1, -100)

    # Kwota równa 0
    with pytest.raises(ValueError):
        bs.wplac(NR_1, 0)

    # Nieistniejace konto
    with pytest.raises(KontoNieIstnieje):
        bs.wplac(NR_2, 100)
