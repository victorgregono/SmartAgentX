# CSV Query Agent – Plataforma Inteligente para Análise de Dados em CSV

Este projeto foi desenvolvido como uma solução inovadora para análise exploratória de dados em arquivos CSV, utilizando inteligência artificial de ponta (LangChain + OpenRouter) e uma interface web moderna baseada em Flask.

## Visão Geral
A plataforma permite que usuários realizem perguntas em linguagem natural sobre seus próprios arquivos CSV, recebendo respostas precisas, técnicas e contextualizadas. O sistema foi projetado para ser flexível, seguro e facilmente adaptável a diferentes cenários de análise de dados.

## Principais Diferenciais
- **Interface web intuitiva**: Upload de múltiplos arquivos CSV e seleção dinâmica para consulta.
- **Respostas em português técnico**: O agente responde sempre em português do Brasil, com terminologia adequada à área de dados.
- **Processamento local e seguro**: Os dados permanecem sob controle do usuário, sendo processados localmente antes do envio de queries ao LLM.
- **Customização total do prompt**: O comportamento do agente pode ser ajustado facilmente via edição do prompt em `src/prompts/agent_prompt_pt.py`.
- **Suporte a múltiplos modelos gratuitos**: Escolha entre diferentes LLMs disponíveis no OpenRouter, conforme sua necessidade.
- **Documentação clara e orientada ao usuário**: Passo a passo detalhado para instalação, configuração e uso.

## Como Executar a Aplicação

Siga o passo a passo profissional abaixo para instalar as dependências e executar a aplicação web:

### 1. Clone o repositório
```powershell
git clone <URL_DO_SEU_REPOSITORIO>
cd csv-agent-project-main
```

### 2. Instale as dependências
Certifique-se de que você possui o Python 3.10+ instalado. Em seguida, execute o comando abaixo para instalar todas as dependências necessárias:
```powershell
pip install -r requirements.txt
```

### 3. Configure sua chave de API do OpenRouter
Obtenha sua chave gratuita em https://openrouter.ai/

Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:
```env
OPENAI_API_KEY=<SUA_API_KEY_AQUI>
OPENAI_API_BASE=https://openrouter.ai/api/v1
```
> **Importante:** A variável `OPENAI_API_KEY` é obrigatória para o funcionamento do sistema. Não compartilhe sua chave publicamente.

### 4. Modelos Gratuitos Disponíveis
- `meta-llama/llama-3.2-3b-instruct:free`
- `microsoft/phi-3-mini-128k-instruct:free`
- `google/gemma-2-9b-it:free`
- `qwen/qwen-2-7b-instruct:free`
- `huggingfaceh4/zephyr-7b-beta:free`

> **Observação:** A disponibilidade dos modelos pode variar conforme o OpenRouter.

### 5. Inicie o servidor web com Flask
Execute o comando abaixo para iniciar a aplicação web:
```powershell
$env:FLASK_APP="src/web_app.py"
python -m flask run
```
O servidor estará disponível em http://127.0.0.1:5000/

### 6. Acesse a interface web
Abra o navegador e acesse http://127.0.0.1:5000/
- Faça upload de arquivos CSV.
- Escolha o modelo de IA.
- Envie perguntas em linguagem natural e visualize respostas detalhadas.

### 7. Limite de Requisições
Os modelos gratuitos possuem limite diário de 50 requisições. Para ampliar, adicione créditos em sua conta OpenRouter.

## Estrutura do Projeto
- `src/web_app.py`: Backend Flask e lógica da interface web.
- `src/agents/csv_agent.py`: Núcleo de processamento inteligente e integração com LLM.
- `src/data/`: Armazene seus arquivos CSV para análise.
- `src/prompts/`: Prompts customizáveis para interação com o LLM.

## Observações e Boas Práticas
- Exemplos de CSV já disponíveis em `src/data/`.
- O sistema foi projetado para ser facilmente expandido para outros formatos de dados.
- O prompt pode ser ajustado para diferentes domínios ou estilos de resposta.
- Para dúvidas, sugestões ou contribuições, utilize o sistema de issues/pull requests.

## Personalização Avançada do Prompt
O arquivo `src/prompts/agent_prompt_pt.py` permite customizar o comportamento do agente, incluindo:
- Estilo de resposta (formal, técnico, resumido, etc.)
- Metodologia de análise de dados
- Restrições de linguagem ou formato

---

**Solução original, desenvolvida com foco em inovação, segurança e experiência do usuário.**