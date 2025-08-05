import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# 🔧 Configurações principais
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL'))

# 📊 Dados do empréstimo
COLATERAL_BTC = float(os.getenv('COLATERAL_BTC'))
BORROW_R = float(os.getenv('BORROW_R'))


# 🔢 Função para calcular o preço do BTC a partir de uma % de LTV
def calcular_preco_btc_por_ltv(ltv_percent: int):
    return BORROW_R / (COLATERAL_BTC * (ltv_percent / 100))


# 💡 Faixas de alerta dinâmicas com base na % de LTV
FAIXA_PERIGO = calcular_preco_btc_por_ltv(78)
FAIXA_ALERTA = calcular_preco_btc_por_ltv(70)
FAIXA_ATENCAO = calcular_preco_btc_por_ltv(60)

# 🌍 API de cotação
COINGECKO_API = os.getenv('COINGECKO_API')
TELEGRAM_API = os.getenv('TELEGRAM_API')


# Envia mensagem pelo Telegram
def send_telegram_message(message):
    url = f"{TELEGRAM_API}{TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    if not response.ok:
        print("Erro ao enviar mensagem:", response.text)


# Calcula o LTV
def calcular_ltv(preco_btc):
    valor_colateral = COLATERAL_BTC * preco_btc
    return (BORROW_R / valor_colateral) * 100


# Pega o preço do BTC
def obter_preco_btc():
    try:
        response = requests.get(COINGECKO_API)
        data = response.json()
        return data['bitcoin']['brl']
    except Exception as e:
        print("Erro ao obter preço do BTC:", e)
        return None


# 🧠 Verifica faixa de risco
def verificar_e_enviar_alerta(preco_btc):
    ltv = calcular_ltv(preco_btc)

    if preco_btc < FAIXA_PERIGO:
        nivel = "🔴 PERIGO"
        msg = f"{nivel}!\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%\n➡️ Seu empréstimo está prestes a ser LIQUIDADO!"  # noqa: E501
    elif preco_btc < FAIXA_ALERTA:
        nivel = "🟠 ALERTA"
        msg = f"{nivel}!\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%\n⚠️ Risco alto! Considere aportar colateral."  # noqa: E501
    elif preco_btc < FAIXA_ATENCAO:
        nivel = "🟡 ATENÇÃO"
        msg = f"{nivel}!\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%\n🔍 Monitoramento sugerido."  # noqa: E501
    else:
        nivel = "✅ SEGURO"
        msg = f"{nivel}\nBTC: R$ {preco_btc:,.2f}\nLTV: {ltv:.2f}%\n👍 Tudo tranquilo no momento."  # noqa: E501

    send_telegram_message(msg)


# 🔁 Loop contínuo
def monitorar():
    while True:
        preco_btc = obter_preco_btc()
        if preco_btc:
            verificar_e_enviar_alerta(preco_btc)
        time.sleep(CHECK_INTERVAL)


# ✅ Iniciar
if __name__ == "__main__":
    monitorar()
