# -*- coding: utf-8 -*-
# https://github.com/cfcGIT/beaconAlarm
#
# Este programa controla los comandos enviados por el administrador al bot de telegram

import telebot
import Proyecto
from daemon import runner

from threading import Thread

import Queue
import sqlite3

import time

TOKEN = '<token>'
DB_STRING = "<database>"

tb = telebot.TeleBot(TOKEN)

with sqlite3.connect(DB_STRING) as con:
  c = con.cursor()
  r = c.execute("SELECT chatid FROM admin")

  for row in r:
    admin_id = str(row[0])

hilos = []

queue = []
proyecto = []

contador_ejecutar = contador_salir = flag_ejecutando = flag_saliendo = 0

tb.send_message(admin_id, "Ejecución iniciada, puedes ejecutar un comando para iniciar el programa")

# Inicia la ejecucion del programa
@tb.message_handler(commands=['ejecutar'])
def ejecutar(message):
  global contador_ejecutar, contador_salir, flag_ejecutando
  if str(message.chat.id) == admin_id:
    if contador_ejecutar == contador_salir:
      flag_ejecutando = 1
      queue.append(Queue.Queue())
      proyecto.append(Proyecto.Proyecto(queue[contador_ejecutar]))
      proyecto[contador_ejecutar].start()
      flag_ejecutando = 0
      contador_ejecutar += 1
    else:
      tb.send_message(message.chat.id, "Debes salir del anterior programa antes de ejecutar otro")
  else:
    tb.send_message(message.chat.id, "No estás autorizado para usar este bot")

# Sale de la ejecucion del programa
@tb.message_handler(commands=['salir'])
def salir(message):
  global contador_ejecutar, contador_salir, flag_saliendo
  if str(message.chat.id) == admin_id:
    if contador_salir == contador_ejecutar - 1 and flag_saliendo == 0:
      flag_saliendo = 1
      queue[contador_salir].put(1)
      time.sleep(10)
      proyecto[contador_salir].exit()
      proyecto[contador_salir].cleanup()
      contador_salir += 1
      flag_saliendo = 0
    else:
      tb.send_message(message.chat.id, "Debes ejecutar el programa antes de salir del mismo")
  else:
    tb.send_message(message.chat.id, "No estás autorizado para usar este bot")

tb.polling()
