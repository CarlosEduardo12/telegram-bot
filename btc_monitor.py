import json
import os
import traceback
import telebot
import requests
from typing import Optional, Dict

from exception_handler import APIError

# Carrega variáveis de ambiente apenas em desenvolvimento
if not os.getenv("GITHUB_ACTIONS"):
    from dotenv import load_dotenv

load_dotenv()

# Configurações
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COINGECKO_API = os.getenv("COINGECKO_API")

# Dados do empréstimo
COLATERAL_BTC = float(os.getenv("COLATERAL_BTC"))
BORROW_R = float(os.getenv("BORROW_R"))

# Inicializa o bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)


class BTCMonitor:
    def __init__(self):
        self.faixa_perigo = self._calcular_preco_btc_por_ltv(78)
        self.faixa_alerta = self._calcular_preco_btc_por_ltv(70)
        self.faixa_atencao = self._calcular_preco_btc_por_ltv(60)

    def _calcular_preco_btc_por_ltv(self, ltv_percent: int) -> float:
        """Calcula o preço do BTC para um determinado LTV."""
        return BORROW_R / (COLATERAL_BTC * (ltv_percent / 100))

    def _calcular_ltv(self, preco_btc: float) -> float:
        """Calcula o LTV atual baseado no preço do BTC."""
        valor_colateral = COLATERAL_BTC * preco_btc
        return (BORROW_R / valor_colateral) * 100

    def obter_preco_btc(self) -> Optional[float]:
        """Obtém o preço atual do BTC."""
        try:
            url = f"{COINGECKO_API}/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "brl"}

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "bitcoin" not in data or "brl" not in data["bitcoin"]:
                raise APIError(f"Resposta da API inválida: {data}")

            return data["bitcoin"]["brl"]

        except requests.exceptions.Timeout:
            print("[ERROR] Timeout ao acessar a API CoinGecko")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Erro na requisição HTTP: {str(e)}")
            return None
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"[ERROR] Erro ao processar resposta da API: {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] Erro inesperado ao obter preço: {str(e)}")
            return None

    def verificar_alertas(self) -> Optional[Dict[str, str]]:
        """Verifica se há necessidade de enviar alertas."""
        preco_btc = self.obter_preco_btc()
        if not preco_btc:
            return None

        ltv = self._calcular_ltv(preco_btc)

        if preco_btc < self.faixa_perigo:
            return {
                "nivel": "🔴 PERIGO",
                "mensagem": f"Seu empréstimo está prestes a ser LIQUIDADO!\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%",
            }
        elif preco_btc < self.faixa_alerta:
            return {
                "nivel": "🟠 ALERTA",
                "mensagem": f"Risco alto! Considere aportar colateral.\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%",
            }
        elif preco_btc < self.faixa_atencao:
            return {
                "nivel": "🟡 ATENÇÃO",
                "mensagem": f"Monitoramento sugerido.\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%",
            }
        return None

    def gerar_relatorio_diario(self) -> Optional[str]:
        """Gera relatório diário com preços min/max e variação."""
        try:
            # API CoinGecko para dados históricos do dia
            url = f"{COINGECKO_API}/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "brl",
                "days": "1",  # Removido o parâmetro interval
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "prices" not in data:
                raise APIError(f"Dados de preços não encontrados. Resposta: {data}")

            # Extrai preços do dia (agora em intervalos de 5 minutos por padrão)
            precos = [price[1] for price in data["prices"]]

            if not precos:
                raise APIError("Lista de preços está vazia")

            preco_atual = precos[-1]  # último preço
            preco_min = min(precos)  # menor preço do dia
            preco_max = max(precos)  # maior preço do dia

            # Calcula variação percentual do dia
            variacao_dia = ((preco_atual - precos[0]) / precos[0]) * 100

            # Calcula variação entre máxima e mínima
            amplitude = ((preco_max - preco_min) / preco_min) * 100

            return (
                "📊 Relatório Diário BTC\n"
                f"Preço Atual: R$ {preco_atual:,.2f}\n"
                f"Mínima: R$ {preco_min:,.2f}\n"
                f"Máxima: R$ {preco_max:,.2f}\n"
                f"Variação 24h: {variacao_dia:+.2f}%\n"
                f"Amplitude: {amplitude:.2f}%"
            )

        except requests.exceptions.Timeout:
            print("[ERROR] Timeout ao acessar dados históricos da API")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Erro na requisição HTTP: {str(e)}")
            return None
        except APIError as e:
            print(f"[ERROR] Erro na API: {str(e)}")
            return None
        except Exception as e:
            print(
                f"[ERROR] Erro inesperado no relatório: {str(e)}\n{traceback.format_exc()}"
            )
            return None
