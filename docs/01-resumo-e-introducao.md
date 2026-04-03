# Resumo e introdução da API ODIN

## Visão geral
A API ODIN é o backend responsável por expor dados escolares processados pelo ETL do projeto. Hoje, o foco principal visível no código é a listagem paginada de escolas, mas a estrutura já aponta para um backend preparado para crescer com novos casos de uso, filtros e endpoints analíticos.

O projeto segue uma organização inspirada em Clean Architecture, com separação entre domínio, aplicação, infraestrutura e apresentação. Isso ajuda a manter o núcleo de regras independente do framework web e da base de dados.

## Stack e base técnica
- Python 3.12
- FastAPI para a camada HTTP
- Motor para acesso assíncrono ao MongoDB
- Pydantic para modelagem e serialização
- dependency-injector para composição de dependências
- Poetry para gestão de dependências e scripts

## Como a API está organizada
A estrutura principal está dividida em quatro camadas:

- `domain`: concentra entidades, enums, value objects, validações e contratos de repositório.
- `application`: contém os casos de uso, como a listagem paginada de escolas.
- `infrastructure`: integra com MongoDB, faz mapeamento entre documento e domínio e concentra a configuração de banco.
- `presentation`: expõe os endpoints FastAPI e faz a ponte entre HTTP e aplicação.

## Fluxo de uma requisição
Quando o endpoint de listagem é chamado, o fluxo acontece assim:

1. A rota FastAPI recebe `page` e `page_size`.
2. O controller cria um DTO de entrada.
3. O caso de uso executa a operação pedindo ao repositório a listagem.
4. O repositório consulta o MongoDB com paginação.
5. O mapper converte documentos do Mongo para objetos de domínio.
6. A resposta é serializada para o formato HTTP esperado.

## Componentes principais
### Entrada da aplicação
O arquivo [src/main.py](src/main.py) monta a aplicação FastAPI, registra o lifespan e faz o wiring do container de dependências.

### Endpoint disponível hoje
O endpoint público atual está em [src/presentation/http/controller/school/list_all_schools_controller.py](src/presentation/http/controller/school/list_all_schools_controller.py). Ele expõe a listagem paginada de escolas sob o prefixo `/api/v1`.

### Caso de uso
O caso de uso de listagem está em [src/application/school/list_all_schools/list_all_schools.py](src/application/school/list_all_schools/list_all_schools.py). Ele é fino por design: recebe um DTO e delega a busca ao repositório.

### Domínio
A entidade principal é [src/domain/entities/school.py](src/domain/entities/school.py). Ela concentra os dados da escola, com validação de domínio e estrutura fortemente tipada.

### Persistência
A implementação Mongo está em [src/infrastructure/database/repository/mongo_school_repository.py](src/infrastructure/database/repository/mongo_school_repository.py). O mapeamento entre documento e objeto de domínio fica em [src/infrastructure/database/mapper/school_mapper.py](src/infrastructure/database/mapper/school_mapper.py).

## O que um novo dev precisa saber primeiro
- O backend ainda está enxuto em termos de endpoints, então a leitura inicial deve começar por `main.py`, depois seguir para o controller, o use case e o repositório.