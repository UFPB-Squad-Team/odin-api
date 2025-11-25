import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """
    Cria uma instância do event loop para o escopo da sessão de testes.
    Necessário para testes assíncronos com motor/fastapi.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()