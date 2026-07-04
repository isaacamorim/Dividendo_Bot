import pytest

from data.validators import validar_fundamentos


def test_dy_absurdo_vira_none_sem_estourar():
    out = validar_fundamentos({"dy": 950, "roe": 21, "preco": 10}, "T")
    assert out["dy"] is None
    assert out["roe"] == 21  # preservado


def test_dy_valido_preservado():
    out = validar_fundamentos({"dy": 8.5, "preco": 10}, "T")
    assert out["dy"] == 8.5


def test_preco_zero_levanta():
    with pytest.raises(ValueError):
        validar_fundamentos({"preco": 0}, "T")


def test_roe_fora_da_faixa_vira_none():
    out = validar_fundamentos({"roe": -250, "preco": 10}, "T")
    assert out["roe"] is None
