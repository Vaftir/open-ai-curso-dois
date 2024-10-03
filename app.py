import os
from time import sleep
from flask import Flask,render_template, request, Response
from openai import OpenAI
from dotenv import load_dotenv
from helpers import *
from selecionar_persona import *
from selecionar_documento import *
from assistente_ecomart import *

load_dotenv()

STATUS_COMPLETED = "completed"
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
modelo = "gpt-4-1106-preview"


app = Flask(__name__)
app.secret_key = 'alura'

#asssitente = criar_assistente()
#thread = criar_thread()
assistente = pegar_json()
thread_id = assistente["thread_id"]
assistente_id = assistente["assistant_id"]
file_ids = assistente["file_ids"]





def bot(prompt):
    maximo_tentativas = 1
    repeticao = 0
    # personalidade = personas[selecionar_persona(prompt)]
    # contexto =selecionar_contexto(prompt)
    # documento_selecionado = selecionar_documento(contexto)



    while True:
        try:
            personalidade = personas[selecionar_persona(prompt)]
            
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

            cliente.beta.threads.messages.create(
               thread_id=thread_id,
               role="user",
               content=prompt,

            )
            run = cliente.beta.threads.runs.create(
               thread_id=thread_id,
               assistant_id=assistente_id
            )

            while run.status != STATUS_COMPLETED:
                run = cliente.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

            historico = list(cliente.beta.threads.messages.list(thread_id=thread_id).data)
            resposta = historico[0]
            return resposta
           
       
        except Exception as erro:
                repeticao += 1
                if repeticao >= maximo_tentativas:
                        return "Erro no GPT: %s" % erro
                print('Erro de comunicação com OpenAI:', erro)
                sleep(1)


@app.route("/chat", methods=["POST"])

def chat():
    prompt = request.json["msg"]
    resposta = bot(prompt)
    #print(resposta)
    texto_resposta = resposta.content[0].text.value
    return texto_resposta

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug = True)
