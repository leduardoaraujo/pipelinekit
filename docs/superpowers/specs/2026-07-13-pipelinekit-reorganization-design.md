# PipelineKit — Design de renomeação e reorganização

**Data:** 2026-07-13  
**Status:** Proposta aprovada para especificação; implementação pendente

## Objetivo

Reposicionar o projeto como uma biblioteca Python modular para construção de pipelines de dados, substituindo a identidade atual ForgeFlow por PipelineKit e organizando o código em torno de quatro responsabilidades principais: fontes, transformações, destinos e execução de pipelines.

O projeto continuará sendo uma biblioteca distribuída via PyPI. Orquestração externa, API HTTP e integração com Airflow serão tratadas como integrações opcionais, não como o centro do pacote.

## Decisões

- Nome público: PipelineKit
- Nome do pacote Python: `pipelinekit`
- Nome da CLI: `pipelinekit`
- Repositório alvo: `leduardoaraujo/pipelinekit`
- Compatibilidade: a migração será documentada; a versão de transição deverá informar como atualizar imports, comando da CLI e configurações.
- Runtime: manter Python 3.11+ e a arquitetura assíncrona existente.
- Integrações: manter Airflow, API e destinos cloud fora do núcleo obrigatório sempre que possível.
- Nome: PipelineKit é o candidato escolhido, embora seja um nome relativamente genérico e já exista em outros projetos; a publicação no PyPI e o uso do novo repositório deverão ser verificados antes do release público.

## Estrutura proposta

```text
pipelinekit/
├── core/             # contratos, modelos, protocolos e exceções
├── sources/          # entradas e conectores de leitura
├── transforms/       # normalização, filtros e mapeamentos
├── destinations/     # saídas e sinks
├── pipeline/         # composição, execução e ciclo de vida
├── config/           # carregamento e validação de configurações
├── integrations/
│   └── airflow/      # integração opcional com Apache Airflow
└── cli/              # comandos de linha de comando
```

A separação deve ser baseada em responsabilidades, não apenas em renomear diretórios. Cada componente deverá depender de contratos em `core/`, evitando que fontes, transformações e destinos dependam diretamente uns dos outros.

A documentação deverá seguir:

```text
docs/
├── getting-started/
├── concepts/
├── guides/
├── reference/
├── examples/
└── integrations/
```

## API conceitual

A API pública deve permitir montar um pipeline sem exigir conhecimento de Airflow ou da CLI. O fluxo conceitual será:

```text
Source → Transform(s) → Destination(s)
                 ↓
             Pipeline.run()
```

Os contratos de fonte, transformação e destino devem permanecer pequenos, tipados e testáveis isoladamente. O executor será responsável por composição, cancelamento, propagação de erros, logging e execução assíncrona.

A CLI e o carregador YAML deverão usar os mesmos modelos públicos da biblioteca, evitando uma segunda representação incompatível da configuração.

## Migração

A implementação será feita em etapas:

1. Inventariar imports, exports, entry points, documentação, testes e configurações que usam `forgeflow`, `ForgeFlow`, `dataforge` ou `data-forge`.
2. Reorganizar os módulos internos para a estrutura proposta, preservando comportamento existente.
3. Atualizar exports públicos, exemplos, CLI, `pyproject.toml`, workflows e documentação.
4. Adicionar testes de importação e execução usando `pipelinekit`.
5. Publicar uma versão de transição com guia de migração e, se tecnicamente viável, aliases temporários para imports antigos.
6. Renomear o repositório para `pipelinekit` e atualizar URLs canônicas.
7. Remover aliases antigos somente após a documentação de migração estar publicada.

Não será feita uma reescrita completa do executor ou dos conectores durante a renomeação. Mudanças funcionais devem ser limitadas ao necessário para criar limites de módulo mais claros.

## Documentação

A página inicial deverá explicar em poucos minutos:

- que PipelineKit é uma biblioteca Python para construir pipelines de dados;
- quais são as quatro abstrações principais;
- um exemplo mínimo em Python;
- um exemplo declarativo em YAML;
- como instalar extras para destinos e integrações;
- como criar uma fonte, transformação ou destino customizado.

A documentação deve remover links quebrados, referências aos nomes anteriores e listas de funcionalidades que contradigam o estado real do código. O changelog deverá separar claramente funcionalidades implementadas, planejadas e mudanças incompatíveis.

## Testes e validação

Antes de considerar a migração concluída:

- a suíte existente deve passar;
- imports públicos devem funcionar com `pipelinekit`;
- o comando `pipelinekit --help` e os comandos principais devem funcionar;
- um pipeline mínimo source → transform → destination deve executar;
- os extras opcionais devem ser verificáveis sem instalar todas as integrações;
- a documentação não deve conter referências residuais aos nomes antigos, exceto no guia de migração;
- o pacote deve ser construído com sucesso;
- os metadados do projeto devem apontar para o novo repositório, documentação e issue tracker.

## Fora de escopo

- criar dashboard web;
- adicionar novos conectores sem relação com a migração;
- transformar PipelineKit em scheduler;
- substituir Airflow;
- dividir imediatamente o projeto em múltiplos pacotes PyPI;
- reescrever toda a API pública por motivos estéticos.

## Critérios de sucesso

A reorganização será considerada bem-sucedida quando um novo usuário conseguir instalar PipelineKit, identificar suas abstrações principais, montar um pipeline mínimo e entender como estendê-lo sem consultar a estrutura interna antiga. O projeto também deverá apresentar uma única identidade consistente em código, documentação, CLI, metadados e repositório.
