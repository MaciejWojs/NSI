import pytest

from API import BankSystem, KontoNieIstnieje


def test_BankSystem():
    bs = BankSystem()
    assert bs is not None


@pytest.fixture(scope="module")
def setup_module():
    numer_konta_pierwszego = "1234567895"
    numer_konta_drugiego = "1111111119"
    bs = BankSystem()
    bs.utworz_konto(numer_konta_pierwszego, "John Doe", 1000)
    bs.utworz_konto(numer_konta_drugiego, "Johnathan Johnson", 1000)
    yield {
        "nr_konta1": numer_konta_pierwszego,
        "nr_konta2": numer_konta_drugiego,
        "bs": bs,
    }
    print("Testy zakończone")


def test_BankSystem_wyplac(setup_module):
    bs = setup_module["bs"]
    assert bs.wyplac(setup_module["nr_konta1"], 100) == 900


def test_BankSystem_wplac(setup_module):
    bs = setup_module["bs"]
    assert bs.wplac(setup_module["nr_konta1"], 200) == 1100


def test_BankSystem_przelew(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    nr2 = setup_module["nr_konta2"]

    assert bs.przelew(nr1, nr2, 100) == 1000
    assert bs.konta[nr2].saldo == 1100


def test_BankSystem_pobierz_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]

    assert bs._pobierz_konto(nr1) is not None
    with pytest.raises(KontoNieIstnieje):
        bs._pobierz_konto("1234567896")


def test_BankSystem_zablokuj_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    bs.zablokuj_konto(nr1)
    assert bs.konta[nr1].status == "zablokowane"


def test_BankSystem_odblokuj_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = setup_module["nr_konta1"]
    bs.odblokuj_konto(nr1)
    assert bs.konta[nr1].status == "aktywne"


def test_BankSystem_zablokuj_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    with pytest.raises(KontoNieIstnieje):
        bs.zablokuj_konto(nr1)


def test_BankSystem_odblokuj_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    with pytest.raises(KontoNieIstnieje):
        bs.odblokuj_konto(nr1)


def test_BankSystem_pobierz_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    with pytest.raises(KontoNieIstnieje):
        bs._pobierz_konto(nr1)


def test_BankSystem_wyplac_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    with pytest.raises(KontoNieIstnieje):
        bs.wyplac(nr1, 100)


def test_BankSystem_wplac_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    with pytest.raises(KontoNieIstnieje):
        bs.wplac(nr1, 100)


def test_BankSystem_przelew_nieistniejace_konto(setup_module):
    bs = setup_module["bs"]
    nr1 = "1234567896"
    nr2 = "1234567897"
    with pytest.raises(KontoNieIstnieje):
        bs.przelew(nr1, nr2, 100)

def test_numer_poprawny(setup_module):
    bs = setup_module["bs"]
    numer = setup_module["nr_konta1"]
    assert bs._numer_poprawny(numer) is True
    assert bs._numer_poprawny("1234567896") is False
    assert bs._numer_poprawny(1234567895) is False
    assert bs._numer_poprawny("1234") is False
    assert bs._numer_poprawny("abcdefghij") is False
