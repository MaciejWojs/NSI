from API import BankSystem
import pytest


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
    print("Teardown module")


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
