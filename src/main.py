#!/usr/bin/env python
"""
App script for sending e-mails to parents for missing children in sports class
Author: Richard Kwasnicki
"""

import kivy
kivy.require('1.10.0')

from functools import partial
from os import path

from smtplib import SMTP

import sqlite3

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox

import config

sm = ScreenManager()
allInputs = []
conn = sqlite3.connect('example.db')
c = conn.cursor()

def initDatabase():
	c.execute('''CREATE TABLE IF NOT EXISTS users (name text, mail text, playgroup text)''')
	c.execute('''CREATE TABLE IF NOT EXISTS trainer (name text, mail text, password text)''')

def sendMailTo(toAddrs, fromAddr, name):
	server = SMTP('smtp.gmail.com:587')
	server.ehlo()
	server.starttls()
	server.login(config.username,config.password)
	msg = "Test Mail an {}".format(name)
	server.sendmail(fromAddr, toAddrs, msg)
	server.quit()

def loadGroups():
	groups = sorted(set([u[2] for u in user]))
	return groups


def saveTheChildren():
	"""
	Insert users to database
	Todo: Encrypt
	"""
	global user
	updateUser()
	# delete old entrys and update with new ones
	c.execute('DELETE FROM users')
	for u in user:
		c.execute('''INSERT INTO users VALUES(?,?,?)''', (u[0], u[1], u[2]))
	conn.commit()

def loadTheChildren():
	"""
	Read users from database
	"""
	global user
	user = []
	for row in c.execute('SELECT * FROM users'):
		user.append((row[0], row[1], row[2]))
	return user

def updateUser():
	"""
	Updates our user info by evaluating the test inputs
	"""
	global user
	user = []
	for inp in allInputs:
		newInfo = [i.text for i in inp]
		if "".join(newInfo) != "":
			user.append(newInfo)
	return user

class UserManager(Screen):
	"""
	Menü zur Eingabe der Nutzer mit Mail und Gruppe
	"""
	def __init__ (self,**kwargs):
		super(UserManager, self).__init__(**kwargs)  
		self.layout = BoxLayout(orientation="vertical")

		loadTheChildren()

		newUser = Button(text="+", size_hint=(1, .2))
		newUser.bind(on_release=self.createNewPlayer)

		backButton = Button(text='Zurück', size_hint=(1, .2))
		backButton.bind(on_release=self.toMenu)

		sc = ScrollView()
		self.users = GridLayout(cols=3, row_default_height='70dp', row_force_default=True, size_hint_y=None)
		self.users.bind(minimum_height=self.users.setter('height'))
		for u in user:
			self.addUser(u)

		sc.add_widget(self.users)
		
		self.layout.add_widget(sc)
		self.layout.add_widget(newUser)
		self.layout.add_widget(backButton)

		self.add_widget(self.layout)

	def addUser(self, entrys):
		"""
		TODO: Change Groups into Dropdown and add extra group management in trainer
		"""
		name = entrys[0]
		mail = entrys[1]
		group = entrys[2]

		nameInput = TextInput(text=str(name), multiline=False)
		self.users.add_widget(nameInput)

		mailInput = TextInput(text=str(mail), multiline=False)
		self.users.add_widget(mailInput)

		groupInput = TextInput(text=str(group), multiline=False, size_hint=(.3, 1))
		self.users.add_widget(groupInput)

		#delButton = Button(text="-")
		#delButton.bind(on_release=self.deleteUser)
		#self.users.add_widget(delButton)

		allInputs.append((nameInput, mailInput, groupInput))

	def deleteUser(self, obj):
		print(obj)

	def toMenu(self, obj):
		saveTheChildren()
		sm.current = "Menu"

	def createNewPlayer(self, obj):
		user.append(("", "", ""))
		self.addUser(user[-1])
		self.layout.do_layout()



class GameManager(Screen):
	"""
	Menü zur Auswahl der aktuellen Gruppe
	-> danach erscheint Liste der zugehörigen Kinder die abgehakt werden kann
	"""
	
	def __init__ (self,**kwargs):
		super(GameManager, self).__init__(**kwargs)  
		self.groupScreens = []
		self.build()

	def build(self):
		self.layout = BoxLayout(orientation="vertical")
		sc = ScrollView()
		scb = GridLayout(cols=1, row_default_height='100dp', row_force_default=True, size_hint_y=None)
		scb.bind(minimum_height=scb.setter('height'))

		for group in loadGroups():
			groupButton = Button(text=group)
			groupButton.bind(on_release=self.toGroup)
			scb.add_widget(groupButton)

		sc.add_widget(scb)
		backButton = Button(text='Zurück', size_hint=(1, .2))
		backButton.bind(on_release=self.toMenu)
		
		self.layout.add_widget(sc)
		self.layout.add_widget(backButton)

		self.add_widget(self.layout)

		loadTheChildren()

		for g in loadGroups():
			if not g in self.groupScreens:
				sm.add_widget(PlayerSelection(name="_{}_".format(g)))
				self.groupScreens.append(g)

	def on_enter(self):
		super(GameManager, self).on_enter(self)
		self.remove_widget(self.layout)
		self.build()

	def toMenu(self, obj):
		sm.current = "Menu"

	def toGroup(self, obj):
		sm.current = "_{}_".format(obj.text)


class PlayerSelection(Screen):
	"""
	Menü zum Anklicken der Kinder
	"""

	def __init__ (self,**kwargs):
		super(PlayerSelection, self).__init__(**kwargs)
		self.groupName = kwargs["name"].replace("_", "")
		self.build()
		

	def build(self):
		self.layout = BoxLayout(orientation="vertical")
		sc = ScrollView()
		self.scb = GridLayout(cols=2, row_default_height='100dp', row_force_default=True, size_hint_y=None)
		self.scb.bind(minimum_height=self.scb.setter('height'))

		self.attend = {}
		self.players = []

		for player in user:
			self.addPlayer(player)
			
		sc.add_widget(self.scb)

		sendButton = Button(text='Sende Mail', size_hint=(1, .2))
		sendButton.bind(on_release=self.submitMails)

		backButton = Button(text='Zurück', size_hint=(1, .2))
		backButton.bind(on_release=self.back)
		
		self.layout.add_widget(sc)
		self.layout.add_widget(sendButton)
		self.layout.add_widget(backButton)

		self.add_widget(self.layout) 

	def on_enter(self):
		super(PlayerSelection, self).on_enter(self)
		self.remove_widget(self.layout)
		self.build()

	def addPlayer(self, player):
		if player[2] == self.groupName:
			playerId = player[0]+"\t"+player[1]
			self.players.append(player)
			self.attend[playerId] = "normal"
			self.scb.add_widget(Label(text=player[0]))
			self.scb.add_widget(CheckBox(on_press=partial(self.togglePlayer, playerId)))

	def togglePlayer(self, playerId, value, **kwargs):
		self.attend[playerId] = value.state

	def back(self, obj):
		sm.current = "Spiel"

	def submitMails(self, obj):
		for playerId in self.attend:
			if self.attend[playerId] == "normal":
				print(playerId)
				# Todo: Send Mail


class TrainerManager(Screen):
	"""
	Menü zur Eingabe der Sendemail + Passwort? + Gruppeneinstellung
	"""
	def __init__ (self,**kwargs):
		super(TrainerManager, self).__init__(**kwargs)  
		layout = BoxLayout(orientation="vertical")

		mailInput = TextInput(text="test@test.de", multiline=False)
		#mailInput.bind(text=updateTrainer)
		layout.add_widget(mailInput)

		passInput = TextInput(text="*******", multiline=False)
		#passInput.bind(text=updateUser)
		layout.add_widget(passInput)

		backButton = Button(text='Zurück', size_hint=(1, .2))
		backButton.bind(on_release=self.back)

		layout.add_widget(backButton)

		self.add_widget(layout)

	def back(self, obj):
		sm.current = "Menu"


class MenuScreen(Screen):
	"""
	Menü zum Wechseln der Screens
	"""

	def __init__ (self,**kwargs):
		super(MenuScreen, self).__init__(**kwargs)  
		layout = BoxLayout(padding=10, orientation="vertical")

		userManagerButton = Button(text='Kinder Manager')
		userManagerButton.bind(on_release=self.switchToUser)

		gameManagerButton = Button(text='Spiel Manager')
		gameManagerButton.bind(on_release=self.switchToGame)

		trainerManagerButton = Button(text='Trainer Manager')
		trainerManagerButton.bind(on_release=self.switchToTrainer)

		exitButton = Button(text='Schließen')
		exitButton.bind(on_release=self.exitApp)


		#myApp.get_running_app().stop()
		layout.add_widget(gameManagerButton)
		layout.add_widget(userManagerButton)
		layout.add_widget(trainerManagerButton)
		layout.add_widget(exitButton)

		self.add_widget(layout)
	
	def switchToUser(self, obj):
		sm.current = "User"

	def switchToGame(self, obj):
		sm.current = "Spiel"

	def switchToTrainer(self, obj):
		sm.current = "Trainer"

	def exitApp(self, obj):
		App.get_running_app().stop()


class KinderMailApp(App):

	def build(self):
		initDatabase()

		km = UserManager(name="User")
		gm = GameManager(name="Spiel")
		tm = TrainerManager(name="Trainer")
		ms = MenuScreen(name="Menu")
		
		sm.add_widget(ms)
		sm.add_widget(km)
		sm.add_widget(gm)
		sm.add_widget(tm)
		return sm

if __name__ == '__main__':
	myApp = KinderMailApp()
	myApp.run()