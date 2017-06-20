# -*- coding: utf-8 -*-
# https://github.com/cfcGIT/beaconAlarm
#
# Este programa ejecuta la funcion principal del sistema: deteccion de intrusos y 
#   envio de mensajes a traves de telegram

import RPi.GPIO as GPIO
import time
import os
import sys
import pygame
from time import gmtime, strftime
from datetime import datetime, timedelta
import sqlite3

# librerias para chequear beacon
import blescan
import bluetooth._bluetooth as bluez

#librerias para mandar telegram
import telebot
import threading

LED_PIN = 16 # Se enciende cuando no es intruso
REDLED_PIN = 26 # Se enciende cuando salta la alarma
GREENLED_PIN = 5 # Encendido mientras se ejecuta el programa
SENSOR_PIN = 21
BUZZER_PIN = 17

SLEEP_ALARM = 0.1
TOKEN_BOT = '<token>' # Token del bot de Telegram
DB_STRING = "<database>"

class Proyecto(threading.Thread):
  def __init__(self, queue):
    super(Proyecto, self).__init__()
    self.queue = queue

    GPIO.setmode(GPIO.BCM) #Configuramos los pines GPIO como BCM
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.setup(REDLED_PIN, GPIO.OUT)
    GPIO.setup(GREENLED_PIN, GPIO.OUT)
    GPIO.setup(SENSOR_PIN, GPIO.IN)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    # Configuramos el bluetooth para chequear beacons
    dev_id = 0
    try:
      self.sock = bluez.hci_open_dev(dev_id)
      self.sock.settimeout(1)
      print "ble thread started"

    except:
      print "error accessing bluetooth device..."
      sys.exit(1)
    
    blescan.hci_le_set_scan_parameters(self.sock)
    blescan.hci_enable_le_scan(self.sock)
    
    self.tb = telebot.TeleBot(TOKEN_BOT)

    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT chatid FROM admin")

      for row in r:
        self.admin_id = str(row[0])
    
    self.flag_exit = 0

  def run(self):
    GPIO.setup(SENSOR_PIN, GPIO.IN)
    GPIO.output(GREENLED_PIN, True)
    time.sleep(5) # sleep inicial

    while True:
      if not self.queue.empty():
        flag_exit = self.queue.get()
        if flag_exit == 1:
          break

      # Comprobamos si se detecta movimiento
      if (GPIO.input(SENSOR_PIN)):
        timex = datetime.now() + timedelta(hours=2) # La hora de la raspberry esta atrasada
    
        # Chequeamos si hay algun beacon cerca
        for i in range(1,3):
          returnedList = blescan.parse_events(self.sock, 10)
          flag = 0
          for beacon in returnedList:
            if beacon != '':
              MAC, UUID, major, minor, TX, RSSI = beacon.split(",")
              # Comprobamos si es un beacon autorizado
              with sqlite3.connect(DB_STRING) as con:
                c = con.cursor()
                r = c.execute("SELECT beacon FROM neighbors")
                for row in r:
                  if UUID == row[0]:
                    MACb, UUIDb, majorb, minorb, TXb, RSSIb = beacon.split(",")
                    flag = 1
                if flag == 1:
                  break
          if flag == 1:
            break
        
        day = format(timex, '%d/%m/%Y')
        hour = format(timex, '%H:%M:%S')

        if (flag == 0):
          # No ha detectado ningun beacon autorizado cerca
          with sqlite3.connect(DB_STRING) as con:
            con.execute("INSERT INTO alerts (intruder, day, hour) VALUES (?, ?, ?)", ["yes", day, hour])
            con.commit()
            c = con.cursor()
            # Enviamos mensaje a los usuarios que hayamos marcado en la web
            r1 = c.execute("SELECT * FROM receiver")

            for row1 in r1:
              chats_ids = []
              if row1[0] == "checked":
                # Enviamos a admin
                query = "SELECT chatid FROM admin"
              elif row1[1] == "checked":
                # Enviamos a ultimo vecino que entro en el garaje
                query = "SELECT chatid FROM neighbors where beacon IN (SELECT q.beacon FROM (SELECT * FROM alerts ORDER BY hour DESC) q where q.intruder='no' ORDER BY q.day DESC limit 1)"
              else:
                # Enviamos a todos
                query = "SELECT chatid FROM admin UNION SELECT chatid FROM neighbors"

              r2 = c.execute(query)
              for row2 in r2:
                chats_ids.append(row2[0])

          # Enviamos mensaje a los destinatarios
          for chat_id in chats_ids:
            mensaje = 'Intruso detectado el dia ' + str(day) + ' a las ' + str(hour)
            self.tb.send_message(chat_id, mensaje)

          # Encendemos el led rojo y hacemos sonar el buzzer
          for i in range(7):
            GPIO.output(REDLED_PIN, True)
            GPIO.output(BUZZER_PIN, True)
            time.sleep(SLEEP_ALARM)
            GPIO.output(REDLED_PIN, False)
            time.sleep(SLEEP_ALARM)
            GPIO.output(REDLED_PIN, True)
            time.sleep(SLEEP_ALARM)
            GPIO.output(REDLED_PIN, False)
            GPIO.output(BUZZER_PIN, False)
            time.sleep(SLEEP_ALARM)

          GPIO.output(REDLED_PIN, False)
          GPIO.output(BUZZER_PIN, False)
        else:
          with sqlite3.connect(DB_STRING) as con:
            con.execute("INSERT INTO alerts VALUES (?, ?, ?, ?)", ["no", day, hour, UUIDb])
            con.commit()

          for i in range(15):
            GPIO.output(LED_PIN, not GPIO.input(LED_PIN))
            time.sleep(0.2)
          GPIO.output(LED_PIN, False)                 
          time.sleep(2)

    self.tb.send_message(self.admin_id, "Se ha salido del programa satisfactoriamente (esperar a que se limpien GPIOs)")
    
  def exit(self):
    # Apagamos todos los GPIOs
    GPIO.output(LED_PIN, False)
    GPIO.output(REDLED_PIN, False)
    GPIO.output(GREENLED_PIN, False)
    GPIO.output(BUZZER_PIN, False)
    # Cerramos la base de datos
    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      c.close()
  
  def cleanup(self):
    GPIO.cleanup()
    self.tb.send_message(self.admin_id, "GPIOs limpios")
