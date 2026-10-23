# Operação e validação no Render de 512 MB

## Comportamento e limites

O perfil padrão usa um worker assíncrono, sem preload, pool MongoDB de até dez
conexões, duas gerações geográficas e um dossiê por vez. Cada classe aceita cinco
operações aguardando por até dez segundos; sobrecarga retorna 503 com
`Retry-After: 10`. Consultas leves e healthchecks não entram nessas filas.

O JSON volumoso é validado por item em arquivo temporário e só começa a ser
enviado depois de estar completo. A representação pública permanece igual,
inclusive o escopo de todos os estados da URL histórica `geojson/paraiba`.
Arquivos são transitórios e removidos após o último leitor, erro ou cancelamento.
Não montar `/tmp` em tmpfs: isso converteria o arquivo temporário em consumo de RAM.
O cache de bytes compartilha 16 MiB por worker; entradas acima de 1 MiB não ficam
em RAM. O registro de gerações compartilhadas tem limite de 32 entradas, incluindo
arquivos completos ainda sendo enviados a leitores lentos.

`GZIP_ENABLED=false` é deliberado. Compare uma execução com `true`, verifique
`Content-Encoding` e consumo de CPU antes de habilitar. A compressão é incremental.
A suspensão por inatividade do Render Free continuará existindo.

## Publicação e rollback

1. Confirmar no painel o comando real e eventuais overrides de `WEB_CONCURRENCY`.
   O comando do contêiner é `gunicorn src.main:app -c gunicorn.conf.py`.
   Definir `WEB_CONCURRENCY=1` e conferir o log `runtime workers=1 preload_app=False`.
2. Capturar logs de falha e métricas anteriores. Diferenciar OOM, timeout e limite
   mensal: a mensagem de limite de serviço sozinha não identifica a causa.
3. Com as credenciais do ambiente configuradas, executar uma vez, antes do deploy:
   `uv run python -m src.infrastructure.database.provision_indexes`.
   O processo não remove índices. Não provisionar índices durante requisições ou
   startup; falha de provisionamento deve ser resolvida antes da publicação.
4. Publicar primeiro o perfil de processo/observabilidade, depois consultas/JSON,
   depois cache/concorrência/PDF. Validar cada imagem antes de avançar. Não é
   necessário alterar a URL do frontend ou o contrato do mapa.
5. Conferir `/health`, `/health/ready`, Bahia, todos os estados, município, bairros
   oficiais, fallback para setores e os dois tipos de dossiê.
6. Havendo regressão funcional ou pressão de memória, restaurar a imagem anterior
   e suas variáveis. Não remover índices no rollback.

Os logs `mongo_cursor` registram tempo aguardando dados e quantidade lida;
`large_json` registra geração, tamanho, cache e concorrência; `request_end`
registra rota, tempo até headers, duração até fim da transmissão, bytes e
`memory_bytes`. A leitura de memória usa cgroup v2/v1 e inclui master, worker e
page cache. Em Windows ou fora de cgroup, o valor pode ser nulo. Não equivale ao
RSS isolado do worker.

## Ensaio isolado de capacidade (Linux/Docker)

Não executar a fixture contra produção. O gerador recusa bancos cujo nome não
começa com `odin_perf_` e também recusa bancos não vazios; não apaga dados.

```bash
docker compose -f compose.performance.yml up -d mongo
docker compose -f compose.performance.yml build api
docker compose -f compose.performance.yml run --rm --volume "$PWD/scripts:/app/scripts:ro" api python -m scripts.seed_performance
docker compose -f compose.performance.yml up -d api
uv run python -m scripts.load_api --users 5 --duration 1800 > capacity-result.json
docker logs odin-perf-api > capacity-api.log
docker inspect odin-perf-api --format '{{.State.OOMKilled}} {{.RestartCount}}'
docker exec odin-perf-api cat /sys/fs/cgroup/memory.peak
```

A fixture contém exatamente 75 mil escolas (27% na Bahia), 1.800 municípios com
polígonos de 1.024 vértices, documentos com e sem centroide, bairros oficiais e
setores para exercitar o fallback. São dados sintéticos: repetir também com uma
cópia anonimizada representativa da base real antes de afirmar capacidade em
produção. O contêiner limita a API a 512 MiB e 0,1 CPU; ajustar CPU se a alocação
efetiva do Render diferir. MongoDB e gerador de carga ficam fora desse orçamento.

O cenário percorre nove UFs, alterna pontos/polígonos, carrega o mapa completo e
produz PDFs. A duração cobre expiração dos TTLs de 60 e 300 segundos. Fazer uma
execução curta inicial para medir separadamente o primeiro acesso. Depois repetir
o ensaio normal com o serviço aquecido. A ferramenta não classifica automaticamente
o tempo de spin-up do Render como latência de consulta.

Aceite: zero OOM, reinícios, JSON incompleto ou 503 em carga normal; memória de
contêiner menor que 400 MB (400.000.000 bytes); p95 aquecido até 2 s para consultas
leves e 5 s para GeoJSON completo. PDFs são reportados separadamente. Inspecionar
também a série de memória nos logs para descartar crescimento contínuo.
O programa sai com erro se houver falhas HTTP ou payload inválido; os limites de
latência/memória precisam ser conferidos no relatório e nos logs. Cache de arquivos
do Linux também conta no limite: não avaliar somente o RSS do Python.

Para saturação, repetir com `--users 20 --duration 60 --think-time 0`; espera-se
sobrecarga controlada com 503 e recuperação após a carga. Não usar os critérios de
zero 503 desse cenário para aprovar/reprovar a carga normal.

Os testes Mongo opcionais são independentes e **removem a coleção escolas** do
banco de testes. Executá-los em outro banco isolado:

```bash
RUN_PERFORMANCE_TESTS=1 MONGO_URI=mongodb://localhost:27018 DATABASE_NAME=odin_perf_queries uv run pytest tests/test_performance_multi_state.py -v
```

Não alterar índices com base apenas em testes sintéticos. Guardar `explain` das
consultas reais (incluindo aliases, UF, município e combinações) e comparar
`nReturned`, `totalDocsExamined`, `totalKeysExamined` e plano vencedor. Só acrescentar
índices quando o ganho estiver demonstrado; esta entrega não cria índices novos
além dos já definidos no projeto.
