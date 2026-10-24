
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from html import escape

import matplotlib
matplotlib.use("Agg")  # Gera imagens sem abrir uma janela gráfica

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel


app = FastAPI(
    title="Fauna API",
    description="Análise temporal de registros de fauna",
    version="1.0.0",
)

# A planilha deve ficar na mesma pasta deste arquivo.
ARQUIVO_EXCEL = Path(__file__).with_name("registros_fauna.xlsx")


def carregar_dados():
    """Lê a planilha e prepara a data e a hora de cada registro."""

    if not ARQUIVO_EXCEL.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Planilha não encontrada: {ARQUIVO_EXCEL.name}",
        )

    try:
        df = pd.read_excel(ARQUIVO_EXCEL)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível ler o Excel: {exc}",
        )

    # Padroniza os nomes das colunas.
    df.columns = df.columns.str.strip().str.lower()

    colunas_necessarias = {"especie", "data", "hora"}
    faltantes = colunas_necessarias - set(df.columns)

    if faltantes:
        raise HTTPException(
            status_code=500,
            detail=f"Colunas ausentes na planilha: {sorted(faltantes)}",
        )

    # Combina data e hora em uma única coluna temporal.
    df["data_hora"] = pd.to_datetime(
        df["data"].astype(str) + " " + df["hora"].astype(str),
        errors="coerce",
    )

    # Descarta registros sem espécie ou horário válido.
    df = df.dropna(subset=["especie", "data_hora"]).copy()
    df["especie"] = df["especie"].astype(str).str.strip()
    df["hora_do_dia"] = (
        df["data_hora"].dt.hour
        + df["data_hora"].dt.minute / 60
        + df["data_hora"].dt.second / 3600
    )

    return df


def filtrar_especie(especie: str):
    """Retorna os registros correspondentes à espécie solicitada."""

    if not especie.strip():
        raise HTTPException(
            status_code=422,
            detail="Informe o nome da espécie.",
        )

    df = carregar_dados()

    registros = df[
        df["especie"].str.casefold() == especie.strip().casefold()
    ]

    if registros.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum registro encontrado para: {especie}",
        )

    return registros


def criar_grafico(registros: pd.DataFrame, tipo: str) -> BytesIO:
    """Gera um histograma ou gráfico circular e retorna um PNG."""

    horas = registros["hora_do_dia"].to_numpy()

    if tipo == "histograma":
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.hist(
            horas,
            bins=np.arange(0, 25, 1),
            edgecolor="black",
        )

        ax.set_xticks(range(0, 24))
        ax.set_xlim(0, 24)
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel("Número de registros")
        ax.set_title("Distribuição horária dos registros")

    elif tipo == "circular":
        fig, ax = plt.subplots(
            figsize=(7, 7),
            subplot_kw={"projection": "polar"},
        )

        # Cada barra representa uma hora do dia.
        contagens, _ = np.histogram(
            horas,
            bins=np.arange(0, 25, 1),
        )

        angulos = np.arange(24) * (2 * np.pi / 24)
        largura = 2 * np.pi / 24

        ax.bar(
            angulos,
            contagens,
            width=largura,
            align="edge",
            edgecolor="black",
            alpha=0.8,
        )

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticks(angulos)
        ax.set_xticklabels([f"{h:02d}h" for h in range(24)])
        ax.set_title("Atividade observada ao longo do dia", pad=20)

    else:
        raise HTTPException(
            status_code=422,
            detail="Tipo inválido. Use histograma ou circular.",
        )

    fig.tight_layout()

    imagem = BytesIO()
    fig.savefig(imagem, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    imagem.seek(0)

    return imagem


# --------------------------------------------------
# OPÇÃO 1: consultar via URL
# --------------------------------------------------

@app.get("/activity")
def atividade(especie: str):
    """Retorna estatísticas e contagens horárias em JSON."""

    registros = filtrar_especie(especie)

    contagens = (
        registros["data_hora"]
        .dt.hour
        .value_counts()
        .reindex(range(24), fill_value=0)
        .sort_index()
    )

    return {
        "especie": especie,
        "total_registros": len(registros),
        "contagens_por_hora": {
            f"{hora:02d}:00": int(total)
            for hora, total in contagens.items()
        },
        "graficos": {
            "histograma": f"/activity.png?especie={quote(especie)}&tipo=histograma",
            "circular": f"/activity.png?especie={quote(especie)}&tipo=circular",
        },
    }


@app.get("/activity.png")
def imagem_atividade(especie: str, tipo: str = "histograma"):
    """Entrega o gráfico solicitado como uma imagem PNG."""

    registros = filtrar_especie(especie)
    imagem = criar_grafico(registros, tipo)

    return StreamingResponse(
        imagem,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


# --------------------------------------------------
# OPÇÃO 2: enviar JSON via HTTPie e pipe
# --------------------------------------------------

class Consulta(BaseModel):
    especie: str
    tipo: str = "histograma"


@app.post("/activity")
def atividade_via_post(consulta: Consulta):
    """Recebe o nome da espécie no corpo JSON."""

    registros = filtrar_especie(consulta.especie)

    # Valida o tipo solicitado e gera a URL do gráfico.
    if consulta.tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo inválido. Use histograma ou circular.",
        )

    contagens = (
        registros["data_hora"]
        .dt.hour
        .value_counts()
        .reindex(range(24), fill_value=0)
        .sort_index()
    )

    return {
        "especie": consulta.especie,
        "total_registros": len(registros),
        "tipo_grafico": consulta.tipo,
        "imagem": (
            f"/activity.png?especie={quote(consulta.especie)}"
            f"&tipo={consulta.tipo}"
        ),
        "contagens_por_hora": [
            {"hora": hora, "registros": int(total)}
            for hora, total in contagens.items()
        ],
    }


# --------------------------------------------------
# OPÇÃO 3: formulário HTML
# --------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Exibe o formulário de consulta."""

    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Atividade da fauna</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 0 20px;
            }
            input, select, button {
                padding: 10px;
                margin: 6px 0;
            }
            img { max-width: 100%; height: auto; }
        </style>
    </head>
    <body>
        <h1>Análise temporal da fauna</h1>
        <form action="/dashboard/result" method="get">
            <label for="especie">Nome científico:</label><br>
            <input id="especie" name="especie"
                   value="Dasyprocta azarae" required><br>

            <label for="tipo">Tipo de gráfico:</label><br>
            <select id="tipo" name="tipo">
                <option value="histograma">Histograma</option>
                <option value="circular">Gráfico circular</option>
            </select><br>

            <button type="submit">Consultar</button>
        </form>
    </body>
    </html>
    """


@app.get("/dashboard/result", response_class=HTMLResponse)
def resultado_dashboard(especie: str, tipo: str = "histograma"):
    """Valida a consulta e apresenta a imagem no navegador."""

    registros = filtrar_especie(especie)

    if tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo de gráfico inválido.",
        )

    url_imagem = (
        f"/activity.png?especie={quote(especie)}&tipo={tipo}"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Resultado da análise</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 30px auto;
                padding: 0 20px;
            }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h1>Atividade observada</h1>
        <p>Espécie: <strong>{escape(especie)}</strong></p>
        <p>Total de registros: {len(registros)}</p>
        <img src="{escape(url_imagem, quote=True)}"
             alt="Gráfico de atividade da espécie">
        <p><a href="/dashboard">Nova consulta</a></p>
    </body>
    </html>
    """
