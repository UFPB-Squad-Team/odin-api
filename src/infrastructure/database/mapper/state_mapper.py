from src.domain.entities.state import State, get_state_name


class StateMapper:
    @staticmethod
    def to_entity(sg_uf: str) -> State:
        sigla = sg_uf.upper()
        nome = get_state_name(sigla) or "Desconhecido"
        return State(id=sigla, nome=nome, sigla=sigla)
