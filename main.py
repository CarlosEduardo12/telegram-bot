import sys
import traceback
import telebot
from datetime import datetime
from btc_monitor import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, BTCMonitor
from exception_handler import ConfigError

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def main():
    try:
        monitor = BTCMonitor()
        now = datetime.now()

        # Relatório diário
        if now.hour == 23 and now.minute < 15:
            relatorio = monitor.gerar_relatorio_diario()
            if relatorio:
                try:
                    bot.send_message(TELEGRAM_CHAT_ID, relatorio)
                except telebot.apihelper.ApiException as e:
                    print(f"[ERROR] Erro ao enviar relatório via Telegram: {str(e)}")

        # Verificação de alertas
        alerta = monitor.verificar_alertas()
        if alerta:
            try:
                mensagem = f"{alerta['nivel']}\n{alerta['mensagem']}"
                bot.send_message(TELEGRAM_CHAT_ID, mensagem)
            except telebot.apihelper.ApiException as e:
                print(f"[ERROR] Erro ao enviar alerta via Telegram: {str(e)}")

    except ConfigError as e:
        print(f"[ERROR] Erro de configuração: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Erro inesperado: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
