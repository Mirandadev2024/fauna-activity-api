import pandas as pd
import sys
from pathlib import Path

import main

# monkeypatch: permite modificar temporariamente um objeto ou variável durante o teste.

def test_carregar_dados(tmp_path, monkeypatch):

    dados = pd.DataFrame({
        "especie": [
            "Dasyprocta azarae",
            "Tapirus terrestris",
            "Dasyprocta azarae"
        ],
        "data": [
            "2026-10-01",
            "2026-10-01",
            "2026-10-02"
        ],
        "hora": [
            "06:30:00",
            "18:15:00",
            "12:00:00"
        ]
    })

    arquivo = tmp_path / "teste.xlsx"

    dados.to_excel(arquivo, index=False)

    monkeypatch.setattr(main, "ARQUIVO_EXCEL", arquivo)

    df = main.carregar_dados()

    assert len(df) == 3
    assert "data_hora" in df.columns
    assert "hora_do_dia" in df.columns
    assert df.iloc[0]["hora_do_dia"] == 6.5
    assert df.iloc[1]["hora_do_dia"] == 18.25


def test_filtrar_especie(tmp_path, monkeypatch):

    dados = pd.DataFrame({
        "especie": [
            "Dasyprocta azarae",
            "Tapirus terrestris",
            "Dasyprocta azarae"
        ],
        "data": [
            "2026-10-01",
            "2026-10-01",
            "2026-10-02"
        ],
        "hora": [
            "06:30:00",
            "18:15:00",
            "12:00:00"
        ]
    })

    arquivo = tmp_path / "teste.xlsx"

    dados.to_excel(arquivo, index=False)

    monkeypatch.setattr(main, "ARQUIVO_EXCEL", arquivo)

    df = main.carregar_dados()

    especies = set(df["especie"])

    for especie in especies:

        registro = main.filtrar_especie(especie)

        assert len(registro) == len(df[df["especie"] == especie])

        assert all(registro["especie"] == especie)

        assert len(main.filtrar_especie("Dasyprocta azarae")) == 2

        assert len(main.filtrar_especie("Tapirus terrestris")) == 1

