# Padrão de módulo repetível

## Objetivo
Este projeto está começando com o domínio `School`, mas a intenção é crescer para outros módulos como `Hospitals`, `Companies` e outros conjuntos de dados. Para não copiar a estrutura inteira de forma manual a cada novo domínio, o ideal é padronizar um esqueleto mínimo de módulo.

## Estrutura recomendada
Cada novo módulo deve seguir a mesma forma lógica:

- `src/domain/entities/<module>.py`
- `src/domain/value_objects/<module_specific>.py`
- `src/domain/validators/<module>_validation.py`
- `src/domain/repository/<module>_repository.py`
- `src/application/<module>/<use_case>/`
- `src/infrastructure/database/mapper/<module>_mapper.py`
- `src/infrastructure/database/repository/<module>_repository.py`
- `src/presentation/http/controller/<module>/`
- `src/presentation/http/controller/<module>/callable/`

## O que deve ser igual em todo módulo
- Um contrato de repositório no domínio.
- Um use case fino na aplicação.
- Um mapper isolando persistência e domínio.
- Um controller HTTP sem regra de negócio.
- Uma rota simples, com validação de query params na borda.
- Respostas de listagem com paginação padronizada.

## O que pode variar por domínio
- Campos do modelo.
- Regras do validador.
- Índices e sort padrão no Mongo.
- DTOs específicos de listagem ou detalhe.

## Regras práticas para não copiar `School` de forma ruim
1. Não duplicar a entidade com o mesmo padrão de `__init__` manual e atributos privados.
2. Preferir modelos Pydantic ou dataclasses com validação declarativa ou pós-validação.
3. Centralizar a paginação Mongo em um helper compartilhado.
4. Reaproveitar a mesma estrutura de testes para todos os módulos.

## Ganho esperado
Com esse padrão, novos módulos entram mais rápido e com menos variação estrutural. Isso reduz retrabalho, facilita revisão por outro dev e deixa o projeto mais previsível para manutenção e escala.