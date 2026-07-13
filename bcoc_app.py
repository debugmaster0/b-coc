#bcoc app.py
import sys									
from PySide6.QtWidgets import (							#widgets
	QApplication,
	QMainWindow,
	QWidget,
	QLabel,
	QPushButton,
	QTextEdit,
	QVBoxLayout,
	QComboBox,
	QHBoxLayout,
	QLineEdit
)
from PySide6.QtCore import Qt
from ledger import EvidenceLedger						  #custom
from blockchain import Blockchain						  #custom
from block import Block						  			  #custom
from cryptography.hazmat.primitives.asymmetric import ec  #for private key place holding
import json   											  #importing ledger events for ledger creation
from io import StringIO 								  #for terminal to output_box printing
import contextlib  										  #for terminal to output_box printing
import qdarkstyle										  #darkmode
import re  												  #used for text input sanitization in add block


#------------UI Format------------
#
#			initialize screen
#			initialize layout QV or QH
#			Titles and subtitles
#           -label-
#			Bottons and boxes
#			Events
#			Add widgets
#			Set layout
#			Update screen
#
#
#			Widget Ordering
#
#			Qlabels - text only
#			QPushButton / QComboBox
#			Layout addWidget - in order of appearence top down
#
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		#generate ledger on start up
		self.users = {}
		self.ledger = EvidenceLedger()
		self.import_events("./events.json", self.users)

		self.setWindowTitle("BCOC Ledger")
		self.setGeometry(300, 200, 600, 400)

		#persistent UI
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)
		self.layout = QVBoxLayout(self.central_widget)

		self.screen_container = QWidget() #updates with button choices via set_screen function
		self.layout.addWidget(self.screen_container)

		self.exit_button = QPushButton("Close App") #persistent
		self.exit_button.clicked.connect(QApplication.quit)
		self.layout.addWidget(self.exit_button)

		self.show_sign_on_screen() #creates sign in layout

#---------Inital screen
	def show_sign_on_screen(self):
		screen = QWidget()
		layout = QVBoxLayout() #vertical layout
		row = QHBoxLayout() #horizontal layout

		title = QLabel("Blockchain Chain of Custody")
		title.setStyleSheet("font-size: 24px; font-weight: bold;")

		subtitle = QLabel("Sign in to continue")

		#sign in screen - dropdown menu - pulls from human IDs (devices cant sign in)
		self.users_dropdown = QComboBox()
		for identity, data in self.users.items():
			if data["type"] == "user":
				self.users_dropdown.addItem(identity)
		row.addWidget(QLabel("user:"))
		row.addWidget(self.users_dropdown)

		#sign in buttons
		button_signin = QPushButton("Sign In")
		button_register = QPushButton("Register User")

		#sign in button event
		button_signin.clicked.connect(self.sign_in_user)
		button_register.clicked.connect(self.register_user)
		
		#widgets
		layout.addWidget(title)
		layout.addWidget(subtitle)
		layout.addWidget(button_signin)
		layout.addWidget(button_register)
		layout.addLayout(row)

		#update screen_container
		screen.setLayout(layout)
		self.set_screen(screen)

#---------Screen that shwos after sign on or registering
	def show_main_menu(self):
		screen = QWidget()
		layout = QVBoxLayout()
		self.recording_dropdown = QComboBox()

		title = QLabel("Main Menu")
		title.setStyleSheet("font-size: 22px; font-weight: bold;")
		title.setAlignment(Qt.AlignHCenter)

		self.output_box = QTextEdit()
		self.output_box.setReadOnly(True)

		#verify menu - dropdown menu
		authorized_records = self.users[self.current_user]["evidence_ids"]
		self.recording_dropdown.addItems(sorted(authorized_records))

		#verify menu buttons
		verify_button = QPushButton("Verify Ledger")
		back_button = QPushButton("Back to Sign On")
		view_button = QPushButton("View Chain of Custody")
		view_button.setEnabled(self.recording_dropdown.count() > 0)
		addblock_button = QPushButton("Add Evidence")

		#button events
		view_button.clicked.connect(self.view_chain_of_custody)
		verify_button.clicked.connect(self.verify_ledger)
		back_button.clicked.connect(self.show_sign_on_screen)
		addblock_button.clicked.connect(self.add_block_menu)
		self.status_label = QLabel("Ready") #will update to verified or compromised

		#widgets
		layout.addWidget(title)
		layout.addWidget(verify_button)
		layout.addWidget(addblock_button)
		layout.addWidget(QLabel("Evidence ID:"))
		layout.addWidget(self.recording_dropdown)
		layout.addWidget(view_button)
		layout.addWidget(self.status_label)
		layout.addWidget(self.output_box)
		layout.addWidget(back_button)

		#update screen_container
		screen.setLayout(layout)
		self.set_screen(screen)

#---------verify ledger uses ledger class fucntion to verify ledger and prints result
	def verify_ledger(self):
		buffer = StringIO() #buffer used to grab print statements to terminal

		with contextlib.redirect_stdout(buffer): #redirects print statements to buffer
			valid = self.ledger.validate_ledger() #valid is True or False for label output context

		self.output_box.setPlainText(buffer.getvalue())  #buffer printed in output_box
		
		if valid:
			self.status_label.setText("Ledger Verified ")
		else:
			self.status_label.setText("Ledger Compromised")

#   Import events and creats a list of users for login simulation purposes
#	Evidence_id is used to access authorized blockchains
#	Identity_id is to aggregate device and human IDs 
#	Private keys and public keys are populated to simulate signatures
#	Type is used to keep track of whether block belongs to device or human
	def import_events(self, in_file, users):
		with open(in_file, "r") as file:
			events = json.load(file)

		for event in events:
			identity_id = event.get("signer_id") or event.get("device_id")
			evidence_id = event["evidence_id"]

			if identity_id not in users:
				private_key = ec.generate_private_key(ec.SECP256R1())
				public_key = private_key.public_key()

				users[identity_id] = {
					"private_key": private_key,
					"public_key": public_key,
					"evidence_ids": set(), 
					"type": "user" if event.get("signer_id") else "device" #have to seperate device uploads from human uploads to make sign in drop down
				}

			users[identity_id]["evidence_ids"].add(evidence_id)

			self.ledger.add_block(
				event,
				users[identity_id]["private_key"],
				users[identity_id]["public_key"]
			)

#---------change screen
	def set_screen(self, screen):  #changes screen_container 
		self.layout.replaceWidget(self.screen_container, screen)
		self.screen_container.deleteLater()
		self.screen_container = screen

#---------change menu from sign in screen to verify menu
	def sign_in_user(self):
		self.current_user = self.users_dropdown.currentText()
		self.show_main_menu()

#---------change screen from sign in to register user
	def register_user(self):
		screen = QWidget()
		layout = QVBoxLayout()

		title = QLabel("Register User")
		title.setStyleSheet("font-size: 22px; font-weight: bold;")

		hint = QLabel(
			"User: Letters, numbers, _, max 24 characters."
		)
		hint.setStyleSheet("color: white; font-size: 12px;")

		self.status_label = QLabel("")

		self.identity_id_input = QLineEdit()
		self.identity_id_input.setPlaceholderText("Example: detective_4")

		#buttons
		submit_button = QPushButton("Add User")
		back_button = QPushButton("Back")

		#button events
		submit_button.clicked.connect(self.submit_user)
		back_button.clicked.connect(self.show_sign_on_screen)

		#widgets
		layout.addWidget(title)
		layout.addWidget(QLabel("User ID"))
		layout.addWidget(self.identity_id_input)
		layout.addWidget(hint)
		layout.addWidget(self.status_label)
		layout.addWidget(submit_button)
		layout.addWidget(back_button)

		screen.setLayout(layout)
		self.set_screen(screen)

#---------add new user to app
	def submit_user(self):

		#input sanitization
		identity = self.identity_id_input.text().strip()

		if not re.fullmatch(r"[A-Za-z0-9_]+", identity) or len(identity) > 24:
			self.status_label.setText(
				"User may only contain letters, numbers, and _. Maximum length is 24."
			)
			return

		#avoid existing users
		if identity in self.users:
			self.status_label.setText("Error: User already exists.")
			return
		#avoid empty user
		if not identity:
			self.status_label.setText("User cannot be empty.")
			return

		#key generation
		private_key = ec.generate_private_key(ec.SECP256R1())
		public_key = private_key.public_key()

		#add user
		self.users[identity] = {
			"private_key": private_key,
			"public_key": public_key,
			"evidence_ids": set(),
			"type": "user"
		}

		self.status_label.setText(f"User {identity} registered successfully ")
		self.identity_id_input.clear()

		#automatic sign in after registering 
		self.current_user = identity 
		self.show_main_menu()

#---------prints a blockchain in verify 
	def view_chain_of_custody(self):
		evidence_id = self.recording_dropdown.currentText()
		chain = self.ledger.get_chain(evidence_id)

		output = f"Chain of Custody for {evidence_id}\n"
		output += "-------------------------------------\n"

		for block in chain.chain:
			output += f"signer_id: {block.signer_id}\n"
			output += f"Action: {block.action}\n"
			output += f"Evidence Hash: {block.evidence_hash}\n"
			output += f"Timestamp: {block.timestamp}\n"
			output += f"Block ID: {block.block_id}\n"
			output += f"Block Hash: {block.block_hash}\n"
			output += f"Previous Hash: {block.previous_hash}\n"
			output += "-" * 40 + "\n"

		self.output_box.setPlainText(output)

#---------Adds block manually, this is skeletonized for convenience 
	def add_block_menu(self):
		screen = QWidget()
		layout = QVBoxLayout()

		title = QLabel("Add Evidence")
		title.setStyleSheet("font-size: 22px; font-weight: bold;")

		self.status_label = QLabel("") 

		#add evidence ID
		self.evidence_id_input = QLineEdit()

		#add evidence action
		self.action_input = QComboBox()
		self.action_input.addItems([
			"Collected",
			"Transferred",
			"Analyzed",
			"Stored"
		])

		self.hash_input = QLineEdit()

		#buttons
		submit_button = QPushButton("Add Block")
		back_button = QPushButton("Back")

		#button events
		submit_button.clicked.connect(self.submit_block)
		back_button.clicked.connect(self.show_main_menu)

		layout.addWidget(title)

		self.evidence_id_input = QLineEdit()
		self.evidence_id_input.setPlaceholderText("Example: evidence_001")
		self.hash_input = QLineEdit()
		self.hash_input.setPlaceholderText("Example: arkfj56")

		hint = QLabel(
			"Existing evidence: hash must match the original.\n"
			"New evidence: enter a unique hash.\n"
			"Evidence: Letters, numbers, _ and -, max 24 characters.\n"
			"Hash : Letters and numbers only, max 24 characters."
			)
		hint.setStyleSheet("color: white; font-size: 12px;")
		layout.addWidget(hint)

		layout.addWidget(QLabel("Evidence ID"))
		layout.addWidget(self.evidence_id_input)

		layout.addWidget(QLabel("Action"))
		layout.addWidget(self.action_input)

		layout.addWidget(QLabel("Evidence Hash"))
		layout.addWidget(self.hash_input)

		layout.addWidget(self.status_label)
		layout.addWidget(submit_button)
		layout.addWidget(back_button)

		screen.setLayout(layout)
		self.set_screen(screen)

#---------adds block from add block menu to ledger, removes spaces
	def submit_block(self):
		evidence_id = self.evidence_id_input.text().strip()
		action = self.action_input.currentText()
		evidence_hash = self.hash_input.text().strip()

		#input regulation
		if not re.fullmatch(r"[A-Za-z0-9_-]+", evidence_id) or len(evidence_id) >24:
			self.status_label.setText(
				"Evidence ID may only contain letters, numbers, _ and - :: MAX length is 24"
			)
			return
		if not re.fullmatch(r"[A-Za-z0-9]+", evidence_hash) or len(evidence_hash) >24:
			self.status_label.setText(
				"Evidence hash may only contain letters and numbers :: MAX length is 24"
			)
			return
	
		event = {
			"evidence_id": evidence_id,
			"action": action,
			"evidence_hash": evidence_hash,
			"signer_id": self.current_user
		}

		chain = self.ledger.get_chain(evidence_id)
		#check that evidence hash matches when uploading to exisiting evidence chain
		if chain is not None:
			original_hash = chain.chain[0].evidence_hash
				
			#make sure hash matches
			if evidence_hash != original_hash:
				self.status_label.setText("Evidence hash mismatch! Block rejected.")
				return

		#add block
		self.ledger.add_block(
			event,
			self.users[self.current_user]["private_key"], self.users[self.current_user]["public_key"]
		)
		#update user authorized records 
		self.users[self.current_user]["evidence_ids"].add(evidence_id)
		self.status_label.setText("Evidence Added - Press back to verify chain ")

# ------- Main -------

def main():
	app = QApplication(sys.argv)
	app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6')) #darkmoode
	app.setQuitOnLastWindowClosed(True) #quit on close
	window = MainWindow()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
