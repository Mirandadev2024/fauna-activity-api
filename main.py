from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from html import escape

import matplotlib
matplotlib.use("Agg")  # Gera imagens sem abrir uma janela gráfica.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel


app = FastAPI(
    title="Fauna API",
    description="Análise temporal de registros de fauna",
    version="1.0.0",
)

# A planilha deve ficar na mesma pasta deste arquivo.
ARQUIVO_EXCEL = Path(__file__).with_name("registros_fauna.xlsx")


# --------------------------------------------------
# PREPARAÇÃO E FILTRAGEM DOS DADOS
# --------------------------------------------------

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

    # Representa a hora como número decimal.
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


def contar_registros_por_hora(registros: pd.DataFrame) -> pd.Series:
    """Conta os registros em cada uma das 24 horas do dia."""

    return (
        registros["data_hora"]
        .dt.hour
        .value_counts()
        .reindex(range(24), fill_value=0)
        .sort_index()
    )


# --------------------------------------------------
# GRÁFICOS MATPLOTLIB (PNG)
# --------------------------------------------------

def criar_grafico_matplotlib(
    registros: pd.DataFrame,
    tipo: str,
) -> BytesIO:
    """Gera um histograma ou gráfico circular e retorna um PNG em memória."""

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
# GRÁFICOS PLOTLY (HTML)
# --------------------------------------------------

def criar_grafico_plotly(
    registros: pd.DataFrame,
    tipo: str,
) -> str:
    """Gera um gráfico interativo com Plotly e retorna um documento HTML."""

    contagens = contar_registros_por_hora(registros)

    # O Plotly recebe um DataFrame com as categorias e suas contagens.
    dados_grafico = pd.DataFrame({
        "hora": [f"{h:02d}h" for h in range(24)],
        "registros": contagens.to_numpy(),
    })

    if tipo == "histograma":
        # Como os dados já estão agrupados por hora, usamos barras.
        fig = px.bar(
            dados_grafico,
            x="hora",
            y="registros",
            title="Distribuição horária dos registros",
            labels={
                "hora": "Hora do dia",
                "registros": "Número de registros",
            },
            template="plotly_white",
        )

    elif tipo == "circular":
        fig = px.bar_polar(
            dados_grafico,
            r="registros",
            theta="hora",
            title="Atividade observada ao longo do dia",
            template="plotly_white",
            category_orders={
                "hora": [f"{h:02d}h" for h in range(24)]
            },
        )

        fig.update_layout(
            polar=dict(
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,
                )
            )
        )

    else:
        raise HTTPException(
            status_code=422,
            detail="Tipo inválido. Use histograma ou circular.",
        )

    fig.update_layout(
        autosize=True,
        margin=dict(l=30, r=30, t=60, b=30),
    )

    # full_html=True permite abrir este endereço diretamente
    # ou carregá-lo em um iframe.
    return fig.to_html(
        full_html=True,
        include_plotlyjs="cdn",
        config={"responsive": True},
    )


# --------------------------------------------------
# OPÇÃO 1: CONSULTA VIA URL (GET)
# --------------------------------------------------

@app.get("/activity")
def atividade(especie: str):
    """Retorna estatísticas e URLs dos gráficos nas duas bibliotecas."""

    registros = filtrar_especie(especie)
    contagens = contar_registros_por_hora(registros)

    especie_url = quote(especie)

    return {
        "especie": especie,
        "total_registros": len(registros),
        "contagens_por_hora": {
            f"{hora:02d}:00": int(total)
            for hora, total in contagens.items()
        },
        "graficos": {
            "matplotlib": {
                "histograma": (
                    f"/activity.png?especie={especie_url}&tipo=histograma"
                ),
                "circular": (
                    f"/activity.png?especie={especie_url}&tipo=circular"
                ),
            },
            "plotly": {
                "histograma": (
                    f"/activity.html?especie={especie_url}&tipo=histograma"
                ),
                "circular": (
                    f"/activity.html?especie={especie_url}&tipo=circular"
                ),
            },
        },
    }


@app.get("/activity.png")
def atividade_matplotlib(especie: str, tipo: str = "histograma"):
    """Entrega o gráfico Matplotlib como imagem PNG."""

    registros = filtrar_especie(especie)
    imagem = criar_grafico_matplotlib(registros, tipo)

    return StreamingResponse(
        imagem,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/activity.html", response_class=HTMLResponse)
def atividade_plotly(especie: str, tipo: str = "histograma"):
    """Entrega o gráfico Plotly como documento HTML."""

    registros = filtrar_especie(especie)
    grafico_html = criar_grafico_plotly(registros, tipo)

    return HTMLResponse(
        content=grafico_html,
        headers={"Cache-Control": "no-store"},
    )


# --------------------------------------------------
# OPÇÃO 2: ENVIAR JSON VIA HTTPie E PIPE
# --------------------------------------------------

class Consulta(BaseModel):
    especie: str
    tipo: str = "histograma"
    biblioteca: str = "matplotlib"


@app.post("/activity")
def atividade_via_post(consulta: Consulta):
    """Recebe a consulta em JSON e informa a URL do gráfico escolhido."""

    registros = filtrar_especie(consulta.especie)

    if consulta.tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo inválido. Use histograma ou circular.",
        )

    if consulta.biblioteca not in {"matplotlib", "plotly"}:
        raise HTTPException(
            status_code=422,
            detail="Biblioteca inválida. Use matplotlib ou plotly.",
        )

    extensao = "png" if consulta.biblioteca == "matplotlib" else "html"
    url_grafico = (
        f"/activity.{extensao}"
        f"?especie={quote(consulta.especie)}&tipo={consulta.tipo}"
    )

    contagens = contar_registros_por_hora(registros)

    return {
        "especie": consulta.especie,
        "total_registros": len(registros),
        "tipo_grafico": consulta.tipo,
        "biblioteca": consulta.biblioteca,
        "url_grafico": url_grafico,
        "contagens_por_hora": [
            {"hora": hora, "registros": int(total)}
            for hora, total in contagens.items()
        ],
    }


# --------------------------------------------------
# OPÇÃO 3: FORMULÁRIO HTML (DASHBOARD)
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

            <label for="biblioteca">Biblioteca:</label><br>
            <select id="biblioteca" name="biblioteca">
                <option value="matplotlib">Matplotlib (PNG)</option>
                <option value="plotly">Plotly (interativo)</option>
            </select><br>

            <button type="submit">Consultar</button>
        </form>
    </body>
    </html>
    """


@app.get("/dashboard/result")
def selecionar_resultado(
    especie: str,
    tipo: str = "histograma",
    biblioteca: str = "matplotlib",
):
    """Direciona a consulta para a página de resultado da biblioteca escolhida."""

    if tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo de gráfico inválido.",
        )

    if biblioteca == "matplotlib":
        destino = "/dashboard/result_matplotlib"
    elif biblioteca == "plotly":
        destino = "/dashboard/result_plotly"
    else:
        raise HTTPException(
            status_code=422,
            detail="Biblioteca inválida. Use matplotlib ou plotly.",
        )

    return RedirectResponse(
        url=f"{destino}?especie={quote(especie)}&tipo={tipo}",
        status_code=303,
    )


@app.get("/dashboard/result_matplotlib", response_class=HTMLResponse)
def resultado_dashboard_matplotlib(
    especie: str,
    tipo: str = "histograma",
):
    """Apresenta o gráfico Matplotlib dentro de uma página HTML."""

    registros = filtrar_especie(especie)

    if tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo de gráfico inválido.",
        )

    url_grafico = (
        f"/activity.png?especie={quote(especie)}&tipo={tipo}"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Resultado Matplotlib</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 30px auto;
                padding: 0 20px;
            }}
            img {{
                display: block;
                max-width: 100%;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <h1>Atividade observada — Matplotlib</h1>
        <p>Espécie: <strong>{escape(especie)}</strong></p>
        <p>Total de registros: {len(registros)}</p>

        <img src="{escape(url_grafico, quote=True)}"
             alt="Gráfico Matplotlib de atividade da espécie">

        <p><a href="/dashboard">Nova consulta</a></p>
    </body>
    </html>
    """


@app.get("/dashboard/result_plotly", response_class=HTMLResponse)
def resultado_dashboard_plotly(
    especie: str,
    tipo: str = "histograma",
):
    """Apresenta o gráfico Plotly interativo dentro de uma página HTML."""

    registros = filtrar_especie(especie)

    if tipo not in {"histograma", "circular"}:
        raise HTTPException(
            status_code=422,
            detail="Tipo de gráfico inválido.",
        )

    url_grafico = (
        f"/activity.html?especie={quote(especie)}&tipo={tipo}"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Resultado Plotly</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 30px auto;
                padding: 0 20px;
            }}
            .grafico {{
                width: 100%;
                min-width: 0;
            }}
            iframe {{
                display: block;
                width: 100%;
                height: 650px;
                border: 0;
            }}
        </style>
    </head>
    <body>
        <h1>Atividade observada — Plotly</h1>
        <p>Espécie: <strong>{escape(especie)}</strong></p>
        <p>Total de registros: {len(registros)}</p>

        <div class="grafico">
            <iframe
                src="{escape(url_grafico, quote=True)}"
                title="Gráfico Plotly de atividade da espécie">
            </iframe>
        </div>

        <p><a href="/dashboard">Nova consulta</a></p>
    </body>
    </html>
    """
