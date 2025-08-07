class BTCMonitorError(Exception):
    """Classe base para exceções do BTCMonitor"""

    pass


class APIError(BTCMonitorError):
    """Exceção para erros de API"""

    pass


class ConfigError(BTCMonitorError):
    """Exceção para erros de configuração"""

    pass
