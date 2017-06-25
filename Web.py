# -*- coding: utf-8 -*-
# https://github.com/cfcGIT/beaconAlarm
#
# Este programa controla toda la funcionalidad de la web a traves de los html alojados en media/

import cherrypy
import webbrowser
import os
import simplejson
import sys
import md5
import sqlite3

MEDIA_DIR = os.path.join(os.path.abspath("."), u"media")
DB_STRING = "<database>"

class Root(object):
  @cherrypy.expose
  def index(self):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    activity_register = ""
    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT q.* FROM (SELECT * FROM alerts ORDER BY hour DESC) q ORDER BY q.day DESC")

      for row in r:
        # Intruder
        if row[0] == "yes":
          activity_register += '''
            <tr class="danger">
              <td>%s - %s</td>
              <td>Detectado intruso dentro del garaje</td>
            </tr>''' %(str(row[1]), str(row[2]))

        # Neighbor
        else:
          activity_register += '''
            <tr class="success">
              <td>%s - %s</td>
              <td>Detectado vecino %s dentro del garaje</td>
            </tr>''' %(str(row[1]), str(row[2]), str(row[3]))

    return open(os.path.join(MEDIA_DIR, u'activity.html')).read() %(activity_register)

  @cherrypy.expose
  def login(self, username, password):
    loc = "/index"
    title = "Error"
    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT * FROM admin")

      for row in r:
        if row[0] == username:
          try:
            if md5.new(password).hexdigest() == row[1]:
              cherrypy.session['userLogin'] = username

              print "SESSION CREATE: %s" %(cherrypy.session['userLogin'])

              loc = "/index"
              title = "Inicio de sesi&oacute;n completado"
              body = "El usuario %s ha iniciado sesi&oacute;n correctamente" %(username)
              return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

            else:
              body = "Constrase&ntilde;a incorrecta"
              return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

          except:
            body = "Constrase&ntilde;a inv&aacute;lida"
            return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

      body = "Usuario %s no registrado en la base de datos" %(username)
      return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

  @cherrypy.expose
  def users(self):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT * FROM neighbors")
      neighbors = ""

      for row in r:
        neighbors += '''
          <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td><button type="button" id="modalBeacon" class="btn btn-primary" data-id="%s" data-toggle="modal" data-target="#modalChangeBeacon">Cambiar beacon asociado</button></td>
            <td><button type="button" class="btn btn-danger" onclick="window.location.href='/deleteUser?username=%s'">Dar de baja</button></td>
          </tr>''' %(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[0]), str(row[0]))

    return open(os.path.join(MEDIA_DIR, u'users.html')).read() %(neighbors)

  @cherrypy.expose
  def changeBeacon(self, username, beacon):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    loc = "/users"
    title = "Error"

    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT username, beacon FROM neighbors")

      for row in r:
        if row[1] == beacon:
          body = "Beacon %s ya asociado a %s" %(row[1], row[0])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

      con.execute("UPDATE neighbors SET beacon = ? WHERE username = ?", [beacon, username])
      con.commit()

    loc = "/users"
    title = "Modificaci&oacute;n realizada"
    body = "Nuevo beacon de %s: %s" %(username, beacon)
    return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

  @cherrypy.expose
  def deleteUser(self, username):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    with sqlite3.connect(DB_STRING) as con:
      con.execute("DELETE FROM neighbors WHERE username = ?", [username])
      con.commit()

    loc = "/users"
    title = "Vecino borrado"
    body = "Vecino %s dado de baja correctamente" %(username)
    return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

  @cherrypy.expose
  def register(self):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    return open(os.path.join(MEDIA_DIR, u'register.html'))

  @cherrypy.expose
  def registerValidate(self, username, email, phone, chatid, beacon, address1, address2, address3):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    loc = "/register"
    title = "Error"

    # Comprobamos que username, email y numero de tfno no estan ya en la base de datos
    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT username, email, phone, chatid, beacon FROM neighbors")

      for row in r:
        #El usuario ya existe en la base de datos
        if row[0] == username:
          body = "El usuario %s ya exite en la base de datos" %(row[0])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        #El email ya existe en la base de datos
        elif row[1] == email:
          body = "El email %s ya est&aacute; registrado en la base de datos" %(row[1])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        #El email ya existe en la base de datos
        elif row[2] == phone:
          body = "El n&uacute; de tel&eacute;fono %s ya est&aacute; registrado en la base de datos" %(row[2])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        #El email ya existe en la base de datos
        elif row[3] == chatid:
          body = "El chatid %s ya est&aacute; registrado en la base de datos" %(row[3])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        #El email ya existe en la base de datos
        elif row[4] == beacon:
          body = "El beacon %s ya est&aacute; asociado a un vecino" %(row[3])
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

    # Comprobamos que introduce un numero de tfno correcto
    if not phone.isdigit() or not len(phone) == 9:
      body = "N&uacute;mero de tel&eacute;fono incorrecto"
      return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

    # Comprobamos que introduce un chatid correcto
    if not chatid.isdigit() or not len(chatid) == 9:
      body = "Chat id incorrecto"
      return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

    # Comprobamos que la direccion es correcta
    if address1.isdigit() and address2.isdigit() and address3.isdigit(): # Faltarian rangos de portales, pisos y numeros
      with sqlite3.connect(DB_STRING) as con:
        con.execute("INSERT INTO neighbors VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [username, email, phone, chatid, address1, address2, address3, beacon])
        con.commit()

      loc = "/users"
      title = "Registro completado"
      body = "Vecino %s dado de alta correctamente" %(username)
      return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

    else:
      body = "Direcci&oacute;n incorrecta"
      return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

  @cherrypy.expose
  def notifications(self):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT * FROM receiver")

      for row in r:
        receiver = '''
          <form>
            <div class="radio">
              <label><input type="radio" name="optradio" value="admin" onclick="window.location.href='/receiverNotifications?option=admin'" %s>Administrador</label>
            </div>
            <div class="radio">
              <label><input type="radio" name="optradio" value="last" onclick="window.location.href='/receiverNotifications?option=last'" %s>&Uacute;ltimo vecino en entrar</label>
            </div>
            <div class="radio">
              <label><input type="radio" name="optradio" value="everybody" onclick="window.location.href='/receiverNotifications?option=everybody'" %s>Todos (vecinos y administrador)</label>
            </div>
          </form>''' %(str(row[0]), str(row[1]), str(row[2]))

    return open(os.path.join(MEDIA_DIR, u'notifications.html')).read() %(receiver)

  @cherrypy.expose
  def receiverNotifications(self, option):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    with sqlite3.connect(DB_STRING) as con:
      if option == "admin":
        con.execute("UPDATE receiver SET admin=?, last=?, everybody=?", ["checked", "", ""])
      elif option == "last":
        con.execute("UPDATE receiver SET admin=?, last=?, everybody=?", ["", "checked", ""])
      else:
        con.execute("UPDATE receiver SET admin=?, last=?, everybody=?", ["", "", "checked"])
      con.commit()

    raise cherrypy.HTTPRedirect('/notifications')

  @cherrypy.expose
  def changePassword(self, current, new1, new2, loc):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    title = "Error"

    with sqlite3.connect(DB_STRING) as con:
      c = con.cursor()
      r = c.execute("SELECT password FROM admin")
      
      for row in r:
        if md5.new(current).hexdigest() != row[0]:
          body = "Contrase&ntilde;a actual incorrecta"
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        if new1 != new2:
          body = "Las contrase&ntilde;as no coinciden"
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

        if len(new1) < 8:
          body = "Contrase&ntilde;a demasiado corta"
          return open(os.path.join(MEDIA_DIR, u'incorrectMsg.html')).read() %(loc, title, body, loc)

      con.execute("UPDATE admin SET password = ?", [md5.new(new1).hexdigest()])
      con.commit()

    title = "Modificaci&oacute;n realizada"
    body = "Contrase&ntilde;a modificada correctamente"
    return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

  @cherrypy.expose
  def logout(self):
    try:
      if cherrypy.session['userLogin'] == "":
        return open(os.path.join(MEDIA_DIR, u'index.html'))
    except:
      return open(os.path.join(MEDIA_DIR, u'index.html'))

    loc = "/index"
    title = "Cierre de sesi&oacute;n completado"
    body = "El usuario %s ha cerrado sesi&oacute;n correctamente" %(cherrypy.session['userLogin'])

    # Borramos la sesion userLogin
    cherrypy.session['userLogin'] = ""

    return open(os.path.join(MEDIA_DIR, u'correctMsg.html')).read() %(loc, title, body, loc)

if __name__ == '__main__':
  config = {
      '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
      },
      '/media': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': MEDIA_DIR
      },
      '/bootstrap': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': MEDIA_DIR+"/bootstrap"
      }
  }

  root = Root()

  cherrypy.config.update({'server.socket_host': '<ip>'})

  cherrypy.quickstart(root, '/', config)
