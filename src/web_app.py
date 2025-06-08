from flask import Flask, request, render_template, redirect, url_for
import os
from agents.csv_agent import CsvAgent
import sys
from pyunpack import Archive
from utils.file_unpacker import unpack_archives
import time
from dotenv import load_dotenv
import html

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
ALLOWED_EXTENSIONS = {'csv', 'zip'}
TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
csv_agent = CsvAgent()

# List of free models available on OpenRouter (ordered by reliability)
FREE_MODELS = [
    "deepseek/deepseek-prover-v2:free",
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
    "nousresearch/nous-capybara-7b:free",
    "openchat/openchat-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    print(f"📝 Rota / acessada")
    print(f"📁 TEMPLATE_FOLDER: {TEMPLATE_FOLDER}")
    print(f"📁 UPLOAD_FOLDER: {UPLOAD_FOLDER}")
    
    files = os.listdir(UPLOAD_FOLDER)
    csv_files = [f for f in files if f.endswith('.csv')]
    print(f"📄 Arquivos CSV encontrados: {csv_files}")
    print(f"🔧 Modelos disponíveis: {len(FREE_MODELS)}")
    
    return render_template('main.html', response=None, files=csv_files, models=FREE_MODELS)

@app.route('/test')
def test():
    return "<h1>Teste OK - Servidor funcionando!</h1>"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        if file.filename.endswith('.zip'):
            unpack_archives(app.config['UPLOAD_FOLDER'])
        csv_agent._load_csvs()  # Reload CSVs
    return redirect(url_for('index'))

@app.route('/query', methods=['POST'])
def query():
    selected_model = request.form.get('model')
    question = request.form.get('question')
    
    print(f"🔍 Nova consulta recebida:")
    print(f"   Modelo: {selected_model}")
    print(f"   Pergunta: {question}")
    
    if not selected_model or not question:
        print("❌ Erro: Modelo ou pergunta não fornecidos")
        return "Erro: Modelo e pergunta são obrigatórios.", 400
    
    files = os.listdir(UPLOAD_FOLDER)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        error_message = "Não há arquivos CSV disponíveis para consulta. Por favor, faça o upload de pelo menos um arquivo CSV."
        print(f"❌ {error_message}")
        return render_template('main.html', response=error_message, files=[], models=FREE_MODELS)

    try:
        print("🤖 Iniciando processamento da consulta...")
        start_time = time.time()
        response = csv_agent.process_query(question, selected_model)
        query_time = round(time.time() - start_time, 2)
        
        print(f"✅ Consulta processada em {query_time}s")
        print(f"📄 Resposta recebida (primeiros 200 chars): {str(response)[:200]}...")
        
        formatted_response = f"Modelo usado: {selected_model}\nPergunta: {question}\n\nResposta ({query_time}s):\n{response}"
        print(f"📝 Resposta formatada criada, tamanho: {len(formatted_response)} chars")
        
    except Exception as e:
        print(f"❌ Erro durante processamento: {str(e)}")
        error_message = f"Erro ao processar sua consulta: {str(e)}"
        
        if "429" in str(e) or "rate limit" in str(e).lower():
            error_message += "\n\n🚫 LIMITE DE REQUISIÇÕES EXCEDIDO"
            error_message += "\n" + "="*50
            error_message += "\n\n📊 Informações sobre limites dos modelos gratuitos:"
            error_message += "\n• Limite diário: 50 requisições por dia"
            error_message += "\n• Status atual: Limite excedido"
            error_message += "\n• Reinício do limite: À meia-noite (UTC)"
            
            if "free-models-per-day" in str(e):
                error_message += "\n\n💰 Para desbloquear mais requisições:"
                error_message += "\n• Adicione 10 créditos no OpenRouter"
                error_message += "\n• Isso aumentará seu limite para 1.000 requisições/dia"
                error_message += "\n• Acesse: https://openrouter.ai/credits"
            
            error_message += "\n\n⏰ Alternativas imediatas:"
            error_message += "\n• Aguarde até a meia-noite (UTC) para reset automático"
            error_message += "\n• Use sua própria chave de API de outros provedores"
            error_message += "\n• Teste com perguntas mais simples quando disponível"
            
            if "X-RateLimit-Remaining" in str(e):
                error_message += "\n\n📈 Detalhes técnicos extraídos do erro:"
                if "'X-RateLimit-Remaining': '0'" in str(e):
                    error_message += "\n• Requisições restantes: 0"
                if "X-RateLimit-Limit" in str(e):
                    error_message += "\n• Limite total: 50 requisições"
        elif "404" in str(e) or "not found" in str(e).lower():
            error_message += "\n\n💡 Dica: Modelo não encontrado. O sistema tentará automaticamente usar um modelo alternativo disponível."
        elif "authentication" in str(e).lower() or "401" in str(e):
            error_message += "\n\n💡 Dica: Problema de autenticação. Verifique se as variáveis de ambiente OPENAI_API_KEY e OPENAI_API_BASE estão configuradas corretamente."
        elif "timeout" in str(e).lower():
            error_message += "\n\n💡 Dica: Timeout na requisição. Tente uma pergunta mais simples ou aguarde alguns minutos."
        elif "Could not parse LLM output" in str(e):
            error_message += "\n\n💡 Dica: Problema no processamento da resposta do modelo. Tente reformular sua pergunta ou escolher outro modelo."
        else:
            error_message += "\n\n💡 Dica: Tente reformular sua pergunta ou selecionar um modelo diferente."
        
        return render_template('main.html', response=error_message, files=csv_files, models=FREE_MODELS)
    
    return render_template('main.html', response=formatted_response, files=csv_files, models=FREE_MODELS)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    print('Iniciando servidor Flask em http://127.0.0.1:5000 ou http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    files = os.listdir(UPLOAD_FOLDER)
    csv_files = [f for f in files if f.endswith('.csv')]
    return render_template('main.html', response="Erro 404: Página não encontrada", files=csv_files, models=FREE_MODELS), 404

@app.errorhandler(500)
def internal_server_error(e):
    files = os.listdir(UPLOAD_FOLDER)
    csv_files = [f for f in files if f.endswith('.csv')]
    return render_template('main.html', response="Erro 500: Erro interno do servidor. Por favor, tente novamente mais tarde.", files=csv_files, models=FREE_MODELS), 500
