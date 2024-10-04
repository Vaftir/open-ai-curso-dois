from flask import Flask,render_template, request, Response
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
from time import sleep
from helpers import *
from selecionar_persona import *
from selecionar_documento import *
from assistente_ecomart import *
from vision_ecomart import analisar_imagem

## CARREGA AS VARIÁVEIS DE AMBIENTE
load_dotenv()

## PARA O STATUS DO RUNNING DO BOT
STATUS_COMPLETED = "completed" 
STATUS_REQUIRES_ACTION = "requires_action"
UPLOAD_FOLDER = 'data'


caminho_imagem_enviada = None


## CRIA O CLIENT E SETA O MODELO
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
modelo = "gpt-4o-mini"


app = Flask(__name__)
app.secret_key = 'alura'

#asssitente = criar_assistente()
#thread = criar_thread()

### CHAMA A FUNÇAO QUE CRIA O ASSISTENTE E A THREAD E OS ARQUIVOS
### SE O ASSISTENTE JÁ EXISTIR ELE NÃO CRIA NOVAMENTE MAS BUSCA O ASSISTENTE JÁ CRIADO DO assistentes.json
assistente = pegar_json()
### PEGA O ID DO THREAD E ASSISTENTE E OS ARQUIVOS E ARMAZENA EM VARIÁVEIS
thread_id = assistente["thread_id"]
assistente_id = assistente["assistant_id"]
file_ids = assistente["file_ids"]





## FUNÇÃO QUE VAI INTERAGIR COM O GPT-4-1106-preview
def bot(prompt):
    global caminho_imagem_enviada
    maximo_tentativas = 1
    repeticao = 0


    ### CHAMA A FUNÇÃO QUE VAI SELECIONAR A PERSONA DE ACORDO COM A MENSAGEM DO USUÁRIO
    while True:
        try:
            personalidade = personas[selecionar_persona(prompt)]
            ### CRIA UMA MENSAGEM NO THREAD COM A PERSONA SELECIONADA para cada mensagem do usuário
            cliente.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content =  f"""
                Assuma, de agora em diante, a personalidade abaixo. 
                gnore as personalidades anteriores.
                # Persona
                {personalidade}
                """
            )
            ### ESSE METODO UTILIZA O VISION PARA ANALISAR A IMAGEM
            resposta_vision = ""
            if caminho_imagem_enviada != None:
                resposta_vision = analisar_imagem(caminho_imagem_enviada)
                resposta_vision = ". Na resposta final, apresente detalhes sobre a imagem. "
                os.remove(caminho_imagem_enviada)
                caminho_imagem_enviada = None

            ## CRIA UMA MENSAGEM NO THREAD COM A MENSAGEM DO USUÁRIO
            cliente.beta.threads.messages.create(
               thread_id=thread_id,
               role="user",
               content=resposta_vision+prompt, ### AQUI EU ESTOU CONCATENANDO A RESPOSTA DO VISION COM A MENSAGEM DO USUÁRIO PARA ENVIAR PARA O GPT-4-1106-preview

            )
            ## CRIA UMA INTERAÇÃO COM O GPT-4-1106-preview PASSANDO O THREAD_ID E O ASSISTENTE_ID
            run = cliente.beta.threads.runs.create(
               thread_id=thread_id,
               assistant_id=assistente_id
            )

            ## ENQUANTO O STATUS DO RUN FOR DIFERENTE DE COMPLETED ELE VAI FICAR AGUARDANDO A RESPOSTA DO GPT
            while run.status != STATUS_COMPLETED:
                run = cliente.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                print(f"Status do Run: {run.status}")

                
   
                
                ## DESVIO DE PROCESSO RESPONSÁVEL GARANTIR QUE EU VOU ABSORVER UM CORPOTAMENTO SE TIVER UMA CHAMADA DE FUNÇÃO
                ## SE TIVER UMA CHAMADA DE FUNÇÃO EU VOU ABSORVER O CORPO DA FUNÇÃO E INTERPRETAR O QUE ESTÁ DENTRO
                if run.status == STATUS_REQUIRES_ACTION:
                    tools_acionadas =       run.required_action.submit_tool_outputs.tool_calls
                    respostas_tools_acionadas = []
                    ## PRECISO PERCORRE TODAS AS FERRAMENTAS QUE FORAM ACIONADAS PARA INTERPRETAR O QUE ESTÁ DENTRO CORRETAMENTE

                    for uma_tool in tools_acionadas:
                            ## BUSCAR O NOME DA FUNÇÃO QUE FOI ACIONADA
                            nome_funcao = uma_tool.function.name
                            ## BUSCAR A FUNÇÃO QUE FOI ACIONADA de acordo com o dicinário de funções em tools_ecomart.py passando o nome da função
                            funcao_escolhida = minhas_funcoes[nome_funcao]
                            ## VERIFICA OS ARGUMENTOS DA FUNÇÃO ACIONADA PELA FERRAMENTA E ARMAZENA EM UMA VARIÁVEL
                            argumentos = json.loads(uma_tool.function.arguments)
                            print(argumentos)
                            ## CHAMA A FUNÇÃO QUE FOI ACIONADA PELA FERRAMENTA E PASSA OS ARGUMENTOS
                            resposta_funcao = funcao_escolhida(argumentos)
                            ### PRECISO RETORNAR A RESPOSTA DA FUNÇÃO PARA O GPT-4-1106-preview

                            respostas_tools_acionadas.append({
                                "tool_call_id": uma_tool.id,
                                "output": resposta_funcao
                            })
                    ## RETORNA A RESPOSTA DAS FERRAMENTAS ACIONADAS para o GPT-4-1106-preview
                    ## submit_tool_outputs é uma função que vai enviar a resposta das ferramentas acionadas para o GPT-4-1106-preview
                    run = cliente.beta.threads.runs.submit_tool_outputs(
                            thread_id = thread_id,
                            run_id = run.id,
                            tool_outputs=respostas_tools_acionadas
                        )
                if run.status == "failed":
                    print("Falha na execução do GPT-4-1106-preview")


                 
            ## LUSTA DE MENSAGENS DO THREAD
            historico = list(cliente.beta.threads.messages.list(thread_id=thread_id).data)
            ## PEGA A ÚLTIMA MENSAGEM DO HISTÓRICO DO THREAD QUE É A RESPOSTA DO BOT
            resposta = historico[0]
            ## RETORNA A RESPOSTA DO BOT
            return resposta
           
       
        except Exception as erro:
                repeticao += 1
                if repeticao >= maximo_tentativas:
                        return "Erro no GPT: %s" % erro
                print('Erro de comunicação com OpenAI:', erro)
                sleep(1)

@app.route('/upload_imagem', methods=['POST'])
def upload_imagem():
    global caminho_imagem_enviada
    if 'imagem' in request.files:
        imagem_enviada = request.files['imagem']
        ## pego o nome do arquivo e a extensão
        nome_arquivo = str(uuid.uuid4()) + os.path.splitext(imagem_enviada.filename)[1]
        ## crio o caminho do arquivo
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        ## salvo o arquivo no caminho especificado
        imagem_enviada.save(caminho_arquivo)
        ## armazeno o caminho do arquivo na variável global
        caminho_imagem_enviada = caminho_arquivo


        return 'Imagem recebida com sucesso!', 200
    return 'Nenhum arquivo foi enviado', 400
    



@app.route("/chat", methods=["POST"])

## FUNÇÃO QUE VAI RECEBER A MENSAGEM DO USUÁRIO E RETORNAR A RESPOSTA DO BOT
def chat():
    prompt = request.json["msg"]
    resposta = bot(prompt)
    texto_resposta = resposta.content[0].text.value
    return texto_resposta

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug = True)
