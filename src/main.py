#!/usr/bin/env python
"""
App script for sending e-mails to parents for missing children in sports class
Author: Richard Kwasnicki
"""

import kivy
kivy.require('1.10.0')

from functools import partial

from email.mime.text import MIMEText
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
from kivy.uix.popup import Popup

import config

def loadTheChildren():
	"""
	Read users from database
	"""
	global user
	user = []
	for row in c.execute('SELECT * FROM users'):
		user.append((row[0], row[1], row[2]))
	return user

class UserManager(Screen):
	"""
	menu for managing the users

	TODO: import csv
	TODO: telefon numbers for sms? 
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
		Idea: Change Groups into Dropdown and add extra group management in trainer
		Todo: Delete Button behind every user
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
		self.saveTheChildren()
		sm.current = "Menu"

	def createNewPlayer(self, obj):
		user.append(("", "", ""))
		self.addUser(user[-1])
		self.layout.do_layout()

	def saveTheChildren(self):
		"""
		Insert users to database
		Todo: Encrypt
		"""
		global user
		self.updateUser()
		# delete old entrys and update with new ones
		c.execute('DELETE FROM users')
		for u in user:
			c.execute('''INSERT INTO users VALUES(?,?,?)''', (u[0], u[1], u[2]))
		conn.commit()

	def updateUser(self):
		"""
		Updates our user info by evaluating the text inputs
		"""
		global user
		user = []
		for inp in allInputs:
			newInfo = [i.text for i in inp]
			if "".join(newInfo) != "":
				user.append(newInfo)
		return user


class GameManager(Screen):
	"""
	menu for selecting the current group
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

		for group in self.loadGroups():
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

		for g in self.loadGroups():
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

	def loadGroups(self):
		self.groups = sorted(set([u[2] for u in user]))
		return self.groups


class PlayerSelection(Screen):
	"""
	menu for managing which child is here
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
		sendButton.bind(on_release=self.askPassword)

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

	def askPassword(self, obj):
		"""
		asks for password for email
		"""
		self.server = SMTP('smtp.gmail.com:587')
		self.server.ehlo()
		self.server.starttls()

		c.execute("Select mail from trainer")
		self.trainerMail= c.fetchone()[0]

		self.popBox = BoxLayout(orientation="vertical")

		self.passInput = TextInput(password=True, multiline=False)
		submit = Button(text="Einloggen")
		submit.bind(on_release=self.loginToMail)

		self.popBox.add_widget(Label(text="Bitte geben sie ihr E-Mail Passwort für ihre Mail ({}) ein:".format(self.trainerMail)))
		self.popBox.add_widget(self.passInput)
		self.popBox.add_widget(submit)

		self.loginPopup = Popup(title='Einloggen',content=self.popBox, size_hint=(.8, .5))
		self.loginPopup.open()

	def loginToMail(self, obj):
		"""
		logs into mail and sends
		"""
		try:
			#login
			self.server.login(self.trainerMail, self.passInput.text)
			print("Login Successful")

			self.loginPopup.dismiss()
			
			mailPopBox = BoxLayout(orientation="vertical")
			self.mailPop = Popup(title='Sende Mail',content=mailPopBox, size_hint=(.8, .5))

			sendToNames = [pId.split("\t")[0] for pId in self.attend if self.attend[pId] == "normal"]
			sendToNames = ", ".join(sendToNames)

			submit = Button(text="Sende Mail")
			submit.bind(on_release=self.sendMails)

			cancel = Button(text="Abbrechen")
			cancel.bind(on_release=self.mailPop.dismiss)
			
			mailPopBox.add_widget(Label(text="Send Mail an die Eltern von: {}".format(sendToNames)))
			mailPopBox.add_widget(submit)
			mailPopBox.add_widget(cancel)

			
			self.mailPop.open()
			
		except Exception as e:
			self.popBox.children[2].text += "\n(Problem bei Login, Bitte erneut versuchen)" 
			self.popBox.do_layout()
			

	def sendMails(self, obj):
		c.execute("Select name from trainer")
		trainerName = c.fetchone()[0]
		for playerId in self.attend:
			if self.attend[playerId] == "normal":
				playerMail = playerId.split("\t")[1]
				playerName = playerId.split("\t")[0]
				subject = "Badminton-Benachrichtigung"
				text = "Dies ist eine automatische Benachrichtigung, dass ihr Kind {} heute nicht zum Badminton erschienen ist.\nLiebe Grüße, {}".format(playerName,trainerName).encode("utf-8")

				msg = MIMEText(text, "plain", "utf-8")
				msg["Subject"] = subject
				msg["From"] = self.trainerMail
				msg["To"] = playerMail

				self.server.send_message(msg)
		self.mailPop.dismiss()
		self.server.quit()
		sm.current="Menu"



class TrainerManager(Screen):
	"""
	menu for changing mail and password of trainer
	"""
	def __init__ (self,**kwargs):
		super(TrainerManager, self).__init__(**kwargs)  
		layout = BoxLayout(orientation="vertical")

		c.execute("select * from trainer")
		results = c.fetchone()
		trainerName = "Max Mustermann"
		trainerMail = "test@test.de"
		if len(results) > 0:
			print(results)
			trainerName = results[0]
			trainerMail = results[1]



		self.nameInput = TextInput(text=trainerName, multiline=False)
		layout.add_widget(self.nameInput)

		self.mailInput = TextInput(text=trainerMail, multiline=False)
		layout.add_widget(self.mailInput)

		submitButton = Button(text='Ändern', size_hint=(1, .2))
		submitButton.bind(on_release=self.submit)

		backButton = Button(text='Zurück', size_hint=(1, .2))
		backButton.bind(on_release=self.back)

		layout.add_widget(submitButton)
		layout.add_widget(backButton)

		self.add_widget(layout)

	def back(self, obj):
		sm.current = "Menu"

	def submit(self, obj):
		c.execute("DELETE FROM trainer")
		c.execute('''INSERT INTO trainer VALUES(?,?)''', (self.nameInput.text, self.mailInput.text))
		conn.commit()
		sm.current = "Menu"


class MenuScreen(Screen):
	"""
	Menu for changing the screens
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
		self.initDatabase()

		km = UserManager(name="User")
		gm = GameManager(name="Spiel")
		tm = TrainerManager(name="Trainer")
		ms = MenuScreen(name="Menu")
		
		sm.add_widget(ms)
		sm.add_widget(km)
		sm.add_widget(gm)
		sm.add_widget(tm)
		return sm

	def initDatabase(self):
		c.execute('''CREATE TABLE IF NOT EXISTS users (name text, mail text, playgroup text)''')
		c.execute('''CREATE TABLE IF NOT EXISTS trainer (name text, mail text)''')
		conn.commit()

if __name__ == '__main__':
	sm = ScreenManager()
	allInputs = []
	conn = sqlite3.connect('example.db')
	c = conn.cursor()

	myApp = KinderMailApp()
	myApp.run()