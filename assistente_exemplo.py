import os
from time import sleep
from flask import Flask,render_template, request, Response
from openai import OpenAI
from dotenv import load_dotenv
from helpers import *
from selecionar_persona import *
from selecionar_documento import *


load_dotenv()

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
modelo = "gpt-4o-mini"
contexto = carrega("data/dados_ecomart.txt")


assistente = cliente.beta.assistants.create(
    name = "Assistente de Atendimento ao Cliente da EcoMart",
    instructions=f"""
        Você é um chatbot de atendimento a clientes de um e-commerce. 
        Você não deve responder perguntas que não sejam dados do ecommerce informado!
        Além disso, adote a persona abaixo para responder ao cliente.
        
        ## Contexto
        {contexto}
        
        ## Persona
        
        {personas["neutro"]}
    """,
    model=modelo,
)


thread = cliente.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "Liste produtos"
        }
    ]
)


cliente.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="da categoria sustentavel"
)

run = cliente.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistente.id
)


while run.status != "completed":
    run = cliente.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    
historico = cliente.beta.threads.messages.list(thread_id=thread.id).data

for message in reversed(historico):
    print(f"role: {message.role}\nConteudo: {message.content[0].text.value}\n\n")


