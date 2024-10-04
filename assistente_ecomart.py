import os
import json
from time import sleep
from flask import Flask,render_template, request, Response
from openai import OpenAI
from dotenv import load_dotenv
from helpers import *
from selecionar_persona import *
from selecionar_documento import *
from tools_ecomart import *


load_dotenv()

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))
# modelo = "gpt-4-1106-preview"
modelo = "gpt-4o-mini"
contexto = carrega("data/ecomart.txt")



def criar_lista_ids():
        lista_ids_arquivos = []

        file_dados = cliente.files.create(
                file=open("data/dados_ecomart.txt", "rb"),
                purpose="assistants"
        )
        lista_ids_arquivos.append(file_dados.id)

        file_politicas = cliente.files.create(
                file=open("data/politicas_ecomart.txt", "rb"),
                purpose="assistants"
        )
        lista_ids_arquivos.append(file_politicas.id)

        file_produtos = cliente.files.create(
                file=open("data/produtos_ecomart.txt","rb"),
                purpose="assistants"
        )

        lista_ids_arquivos.append(file_produtos.id)

        return lista_ids_arquivos


def criar_vector():
    lista_ids_arquivos = criar_lista_ids()
    vector_store = cliente.beta.vector_stores.create(
            name="Product Documentation",
            file_ids=lista_ids_arquivos
        )
    print(vector_store.id)
    return vector_store.id

# código omitido…

def pegar_json():
        filename = "assistentes.json"

        if not os.path.exists(filename):
                thread_id = criar_thread()
                file_id_list = criar_vector()
                assistant_id = criar_assistente(file_id_list)
                data = {
                        "assistant_id": assistant_id.id,
                        "thread_id": thread_id.id,
                        "file_ids": file_id_list
                }

                with open(filename, "w", encoding="utf-8") as file:
                        json.dump(data, file, ensure_ascii=False, indent=4)
                print("Arquivo 'assistentes.json' criado com sucesso.")

        try:
                with open(filename, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        return data
        except FileNotFoundError:
                print("Arquivo 'assistentes.json' não encontrado.")
       


def criar_thread():
    return cliente.beta.threads.create()

from tools_ecomart import *

# código omitido…
from tools_ecomart import *

# código omitido…

def criar_assistente(file_ids):
        assistente = cliente.beta.assistants.create(
                name="Atendente EcoMart",
                instructions = f"""
                                Você é um chatbot de atendimento a clientes de um e-commerce. 
                                Você não deve responder perguntas que não sejam dados do ecommerce informado!
                                Além disso, acesse os arquivos associados a você e a thread para responder as perguntas.
                                """,
                model = modelo,
                tools= minhas_tools,
                tool_resources={
                    "file_search": {
                           "vector_store_ids": [file_ids]
                    }
                }
        )
        return assistente



