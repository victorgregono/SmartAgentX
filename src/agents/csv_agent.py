import os
import zipfile
import pandas as pd
from langchain_openai import OpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from prompts.agent_prompt_pt import CSV_AGENT_PROMPT_TEMPLATE
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class CsvAgent:
    def __init__(self):
        self.dataframes = {}
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self._unpack_archives()
        self._load_csvs()
        
        # Don't create LLM instance in __init__ - create it when needed
        # Usando o prompt personalizado em português do template
        from prompts.agent_prompt_pt import CSV_AGENT_PROMPT_TEMPLATE
        self.custom_prompt = CSV_AGENT_PROMPT_TEMPLATE
        
        # Check if environment variables are set
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_base = os.environ.get('OPENAI_API_BASE')
        
        if not self.api_key or not self.api_base:
            print("⚠️  Aviso: Variáveis de ambiente OPENAI_API_KEY e/ou OPENAI_API_BASE não estão definidas.")
            print("   Defina-as antes de fazer consultas.")
        else:
            print("✅ Variáveis de ambiente configuradas corretamente.")

    def _unpack_archives(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        for file in os.listdir(self.data_dir):
            if file.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(self.data_dir, file), 'r') as zip_ref:
                    zip_ref.extractall(self.data_dir)

    def _load_csvs(self):
        for file in os.listdir(self.data_dir):
            if file.endswith('.csv'):
                # Load full dataframe without sampling
                try:
                    df = pd.read_csv(os.path.join(self.data_dir, file), encoding='latin1', on_bad_lines='skip')
                    self.dataframes[file] = df
                except (UnicodeDecodeError, pd.errors.ParserError) as e:
                    print(f"Erro ao carregar {file}: {e}")

    def create_agent_with_fallback(self, llm, df, filename):
        """Create an agent with fallback handling for parsing errors"""
        try:
            # First attempt: Use standard agent
            agent = create_pandas_dataframe_agent(
                llm, df, verbose=False, allow_dangerous_code=True, 
                prefix=self.custom_prompt
            )
            print(f"Agente padrão criado com sucesso para {filename}")
            return agent, "standard"
        except Exception as e:
            print(f"Erro ao criar agente padrão para {filename}: {e}")
            try:
                # Fallback: Use agent without custom prompt
                agent = create_pandas_dataframe_agent(
                    llm, df, verbose=False, allow_dangerous_code=True
                )
                print(f"Agente fallback (sem prompt customizado) criado para {filename}")
                return agent, "fallback"
            except Exception as e2:
                print(f"Erro ao criar agente fallback para {filename}: {e2}")
                raise e2

    def execute_query_with_retry(self, agent, query, filename, max_retries=3):
        """Execute query with retry logic for parsing errors"""
        for attempt in range(max_retries):
            try:
                print(f"Tentativa {attempt + 1} para {filename}")
                result = agent.invoke({"input": query})
                
                # Check if result has the expected structure
                if isinstance(result, dict) and 'output' in result:
                    print(f"Sucesso na tentativa {attempt + 1} para {filename}")
                    return result['output']
                elif isinstance(result, str):
                    print(f"Resultado direto obtido para {filename}")
                    return result
                else:
                    print(f"Formato de resultado inesperado para {filename}: {type(result)}")
                    return str(result)
                    
            except ValueError as ve:
                if "Could not parse LLM output" in str(ve):
                    print(f"Erro de parsing na tentativa {attempt + 1} para {filename}: {ve}")
                    if attempt == max_retries - 1:
                        # Last attempt - try with a simpler query
                        try:
                            simple_query = f"Analise os dados e responda: {query}"
                            result = agent.invoke({"input": simple_query})
                            if isinstance(result, dict) and 'output' in result:
                                return result['output']
                            return str(result)
                        except:
                            return f"Não foi possível processar a consulta para {filename} devido a problemas de parsing do modelo."
                else:
                    raise ve
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Erro na tentativa {attempt + 1} para {filename}: {e}")
        
        return f"Não foi possível processar a consulta para {filename} após {max_retries} tentativas."

    def find_available_model(self, preferred_model=None):
        """Find the first available model from a list of options"""
        # List of backup models to try (ordered by reliability)
        backup_models = [
            "deepseek/deepseek-prover-v2:free",           # Usually very reliable
            "google/gemma-2-9b-it:free",                  # Good stability
            "meta-llama/llama-3.2-3b-instruct:free",     # Popular choice
            "microsoft/phi-3-mini-128k-instruct:free",   # Microsoft model
            "mistralai/mistral-7b-instruct:free",        # Mistral AI
            "qwen/qwen-2-7b-instruct:free",              # Alibaba model
            "nousresearch/nous-capybara-7b:free",        # Alternative option
            "openchat/openchat-7b:free",                 # Additional backup
            "huggingfaceh4/zephyr-7b-beta:free"          # Final fallback
        ]
        
        # First try the preferred model if provided
        if preferred_model:
            print(f"Usando modelo solicitado: {preferred_model}")
            return preferred_model
        
        # If no preferred model, return the first backup model
        print(f"Nenhum modelo específico solicitado, usando padrão: {backup_models[0]}")
        return backup_models[0]

    def process_query(self, query, model=None):
        # Check if environment variables are set
        if not self.api_key or not self.api_base:
            return "Erro: Variáveis de ambiente OPENAI_API_KEY e OPENAI_API_BASE não estão definidas. Configure-as e reinicie o aplicativo."
        
        # Find an available model
        print(f"Modelo solicitado: {model}")
        available_model = self.find_available_model(model)
        
        # Create a new instance of OpenAI with the available model
        llm = None
        models_to_try = [
            available_model,
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
        
        # Try models until one works
        for model_to_try in models_to_try:
            if model_to_try is None:
                continue
            try:
                print(f"Tentando criar LLM com modelo: {model_to_try}")
                
                # Create LLM with explicit parameters for OpenRouter
                llm = OpenAI(
                    openai_api_key=self.api_key,
                    openai_api_base=self.api_base,
                    model=model_to_try,
                    temperature=0
                )
                available_model = model_to_try
                print(f"LLM criado com sucesso para o modelo: {available_model}")
                break
            except Exception as e:
                print(f"Erro ao criar LLM com {model_to_try}: {e}")
                continue
        
        if llm is None:
            return "Erro: Não foi possível configurar nenhum modelo de linguagem. Verifique sua conexão e chave API."
        
        # Recrie os agentes com o novo modelo usando fallback
        temp_agents = {}
        agent_types = {}
        
        for file, df in self.dataframes.items():
            try:
                print(f"Criando agente para {file} com {len(df)} linhas")
                agent, agent_type = self.create_agent_with_fallback(llm, df, file)
                temp_agents[file] = agent
                agent_types[file] = agent_type
                print(f"Agente ({agent_type}) criado com sucesso para {file}")
            except Exception as e:
                print(f"Erro ao criar agente para {file}: {e}")
                return f"Erro ao criar agente para {file}: {str(e)}"
            
        # Try to answer using all loaded CSVs with retry logic
        results = {}
        errors = []
        
        # Primeiro, colete todas as respostas usando retry
        for file, agent in temp_agents.items():
            try:
                print(f"Processando arquivo: {file} (tipo: {agent_types[file]})")
                result = self.execute_query_with_retry(agent, query, file)
                results[file] = result
                print(f"Sucesso ao processar {file}")
            except Exception as e:
                # Log more detailed error information
                error_type = type(e).__name__
                error_details = str(e)
                print(f"Erro detalhado ao processar {file}: {error_type} - {error_details}")
                print(f"Traceback completo: {traceback.format_exc()}")
                
                # Check for specific error types
                if "rate limit" in error_details.lower() or "429" in error_details:
                    errors.append(f"Erro ao processar {file}: Limite de requisições excedido")
                elif "authentication" in error_details.lower() or "401" in error_details:
                    errors.append(f"Erro ao processar {file}: Problema de autenticação")
                elif "timeout" in error_details.lower():
                    errors.append(f"Erro ao processar {file}: Timeout na requisição")
                elif "404" in error_details or "not found" in error_details.lower():
                    errors.append(f"Erro ao processar {file}: Modelo não encontrado ou não disponível")
                elif "endpoints" in error_details.lower():
                    errors.append(f"Erro ao processar {file}: Modelo temporariamente indisponível")
                elif "Could not parse LLM output" in error_details:
                    errors.append(f"Erro ao processar {file}: Problema de parsing na resposta do modelo")
                else:
                    errors.append(f"Erro ao processar {file}: {error_type} - {error_details}")
        
        # Se não conseguiu processar nenhum arquivo, retorne os erros
        if not results and errors:
            return "Não foi possível processar sua consulta:\n" + "\n".join(errors)
        
        # Combina as respostas de forma coerente
        combined_response = f"Resultado da análise (usando modelo: {available_model}):\n\n"
        for file, response in results.items():
            combined_response += f"Dados de: {file}\n"
            combined_response += f"{response}\n\n"
            
        # Se houver erros, adiciona ao final
        if errors:
            combined_response += "Observações:\n" + "\n".join(errors)
            
        return combined_response
