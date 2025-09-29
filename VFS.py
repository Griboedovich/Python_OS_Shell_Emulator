import gi # модкль для работы с API связанных с PyGObject который содержит GTK
import sys
import xml.etree.ElementTree as ET
#import base64

gi.require_version("Gtk", "4.0") # подключает пространство имён Gtk версии 4
from gi.repository import Gtk, GLib

class Directory():
	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.childs = []
	def addChild (self,child):
		self.childs.append(child)
	def getName(self):
		return self.name
	def getChilds(self):
		return self.childs

class File():
	def __init__(self, name, f_type, data, parent):
		self.name = name
		self.type = f_type
		self.data = data
		self.parent = parent
	def toString(self):
		return f"{self.name}.{self.type}"

class VfsTerminal(Gtk.ApplicationWindow):
	def __init__(self, **kargs):
		super().__init__(**kargs, title = "VFS")
		self.set_default_size (600, 400)

		self.vfs_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)
		self.set_child(self.vfs_box)

		self.SYSTEM = "system > "
		self.USER = "user > "
		self.SCRYPT = "srypt > "

		self.root_directory = None
		self.current_directory = None

		self.created_history()
		self.created_input()

		self.vfs_buffer.set_text(self.SYSTEM + "WELCOME TO MUSHROOM VFS")

		GLib.timeout_add(20, self.terminal_configuration)

	def created_history(self):
		# создаём текстовое поле в всё окно
		self.vfs_history= Gtk.TextView()
		# подключаем возможность скролить окно
		scrolled = Gtk.ScrolledWindow()
		scrolled.set_child(self.vfs_history)

		scrolled.props.hexpand = True
		scrolled.props.vexpand = True	

		self.vfs_box.append(scrolled)
		# видимость курсора всегда включена
		self.vfs_history.set_cursor_visible(True)
		# отключаем возможность редактировать поле
		self.vfs_history.set_editable(False)
		
		self.vfs_buffer = self.vfs_history.get_buffer()		

	def created_input(self):

		self.vfs_input = Gtk.Entry()
		self.vfs_input.set_text("user > ")

		self.vfs_input.connect("activate", self.on_input_activate)

		self.vfs_box.append(self.vfs_input)	
	
		self.set_focus(self.vfs_input)
		self.vfs_input.set_position(7)

	def on_input_activate(self, vfs_input):
		
		command_line = self.vfs_input.get_text()
		vfs_input.set_text(self.USER)
		vfs_input.set_position(7)
		#print(command_line) #для отладки
		self.vfs_history_input(command_line)
		
		self.vfs_terminal(command_line)

	def vfs_history_input(self, text, text_source = "", prev_char = "\n", next_char = ""):

		end_iter = self.vfs_buffer.get_end_iter()		
		self.vfs_buffer.insert(end_iter, prev_char + text_source + text + next_char)

		print(text_source + text)
	
		# при вызове scroll to iter сразуц после вставки
		# в текстовый буфер, он может ввести себя некоректно
		# для этого мы помещаем эту функцию в очередь на исполнение
		# после событий вставки тексты, перерисовки слоёв, создания
		# новой геометрии текста и тд
		GLib.idle_add(self._auto_scroll_to_queue)

	def _auto_scroll_to_queue(self):

		view_iter = self.vfs_buffer.get_end_iter()
		#перемещаем курсор в начало строки
		view_iter.backward_line()
		view_iter.forward_line()

		self.vfs_history.scroll_to_iter(view_iter, 0, True, 0, 0)
		#отключает функцию от очереди событий Gtk
		return False

	def vfs_terminal(self, command_line):

		sourse, command, args_list, error_check = self.vfs_parser(command_line)
	
		if error_check == "пусто":
			self.vfs_history_input("Введена пустая строка", self.SYSTEM)			
			return
		elif error_check == "источник":
			self.vfs_history_input("Неккоректный источник ввода", self.SYSTEM)			
			return
		elif error_check == "кавычка":
			self.vfs_history_input("Фокусы с кавычками запрещены на территории даного терминала", self.SYSTEM)			
			return
		elif error_check != "":
			self.vfs_history_input("Неизвестная ошибка, как вы вообще получили это сообщение?", self.SYSTEM)			
			return

		if ( not sourse in (self.USER, self.SCRYPT)):
			self.vfs_history_input("Неккоректный источник", self.SYSTEM)
			return
		
		if command == "":
			 return

		if command == "exit":
			self.c_exit(command, args_list)
		elif command == "ls":
			self.c_ls(command, args_list)
		elif command == "cd":
			self.c_cd(command, args_list)
		elif command == "tree":
			self.c_tree(command, args_list)
		else:
				self.vfs_history_input("Неизвестная команда: " + command, self.SYSTEM)

	def vfs_parser(self, command_line):
		sourse = ""
		command = ""

		args_list = []
		argument = ""

		error_check = ""

		space_flag = False
		sign_flag = False	
		index = -1
		# отсутсвие источника
		if len(command_line) == 0:
			error_check = "пусто"
			return sourse,command,args_list, error_check
		
		index = command_line.find(">")
		# парсер источника
		if index == -1:
			error_check = "источник"
			return sourse, command, args_list, error_check
		elif (len(command_line) < index + 2) or (command_line [index + 1] != " "):
			error_check = "источник"
			return sourse, command, args_list, error_check
		else:
			sourse = command_line[:index + 1] + command_line[index + 1]
		#пустой ввод
		if len(command_line) == index + 2:
			return sourse, command, args_list, error_check
		# обрезаем источник
		command_line = command_line[index + 2:]
		# извлечение команды
		space_flag = False
		for i in range(len(command_line)):
			if command_line[i] != " ":
				space_flag = True
				command += command_line[i]
			elif (space_flag):
				index = i;
				break
			index = i
		#обрезаем команду
		command_line = command_line[index:]
		
		# в строке только команда
		if len(command_line) == 1:
			return sourse, command, args_list, error_check

		space_flag = False
		sign_flag = False
		sign_argument = False
		for i in range(len(command_line)):
			if command_line[i] != " " and command_line[i] != '"':
				space_flag = True
				argument += command_line[i]
			elif command_line[i] == '"':
				if (sign_flag):
					sign_flag = False
				else:
					sign_argument = True
					sign_flag = True
			elif (sign_flag):
				argument += " "
			elif (space_flag):
				if sign_argument:
					argument = "'" + argument + "'"
					sign_argument = False
				args_list.append(argument)
				argument = ""
				space_flag = False
		if argument != "":
			if sign_argument:
					argument = "'" + argument + "'"
					sign_argument = False
			args_list.append(argument)
			argument = ""

		#кавычка не закрылась
		if sign_flag:
			error_check = "кавычка"
			return sourse, command, args_list, error_check
	
		return sourse, command, args_list, error_check

	def c_exit(self, command, args_list):
		
			if len(args_list) == 0:
				self.get_application().quit()
			else:
				self.vfs_history_input("Неожиданные аргументы у команды exit: " + " ".join(args_list[0:]), self.SYSTEM)

	def c_ls(self, command, args_list):

		args = ["-l", "-t", "-a"]		

		if len(args_list) == 0:
			self.vfs_history_input("ls", self.SYSTEM)
		else:	
			result_line = "ls "
			error_line = "Неверные аргументы у команды ls:"
			error_check = False
			for i in args_list:
				if i in args:
					result_line += " " + i
				else:
					error_check = True
					error_line += " | " + i
			if error_check:
				self.vfs_history_input(error_line + " |", self.SYSTEM)
			else:
				self.vfs_history_input(result_line, self.SYSTEM)

	def c_cd(self, command, args_list):

		args = ["-P", "-L", "-e"]		

		if len( args_list ) == 0:
			self.vfs_history_input("cd", self.SYSTEM)
		else:	
			result_line = ""
			file_line = ""
			args_line = "cd "
			error_line = "Неверные аргументы у команды cd:"
			error_check = False
			for i in args_list:
				if i [0] == "-":
					if i in args:
						args_line += " " + i
					else:
						error_check = True
						error_line += " | " + i
				elif file_line != "":
					error_line = "| Слишком много аргументов"
					error_check = True
					break
				else:
					file_line = " ---open--> " + i
			if error_check:
				self.vfs_history_input(error_line + " |", self.SYSTEM)
			else:
				result_line = args_line + file_line
				self.vfs_history_input(result_line, self.SYSTEM)

	def c_tree(self, command, args_list):
	
		if len(args_list) == 0:
			if self.current_directory == None:
				self.vfs_history_input("Виртуальная файловая система не подключена", self.SYSTEM)
			else:
				
				self.vfs_history_input("\n" + self.c_tree_logic("-"), self.SYSTEM)
		else:
			self.vfs_history_input("Неожиданные аргументы у команды tree: " + " ".join(args_list[0:]), self.SYSTEM)

	def c_tree_logic(self, indent):
		text = indent
		directory = self.current_directory
		text += directory.getName()

		indent += "-" * 4

		for child in directory.getChilds():
			text += '\n'

			if type(child) == Directory:
				self.current_directory = child
				text += self.c_tree_logic(indent)
				self.current_directory = directory
			else:
				text += indent + child.toString()
		return text

	def terminal_configuration(self):

		parameters = sys.argv

		if len(parameters) == 1:
			return
		elif len(parameters) > 3:
			self.vfs_history_input("Слишком много аргументов конфигурации", self.SYSTEM)
			return
		elif len(parameters) < 3:
			self.vfs_history_input("Не хватает аргументов конфигурации", self.SYSTEM)
			return

		self.vfs_history_input("MUSHROOM VFS запущен со следующими аргументами:    1 - '" + parameters[1] + "'     2 - '" + parameters[2]+ "'" , self.SYSTEM)


		try:
			with open(parameters[1], "r") as vfs:
				pass

		except:

			self.vfs_history_input("Файл виртуальной файловой системы не найден", self.SYSTEM)
			return

		#=================
		if (parameters[1][-4:]) != ".xml":
			self.vfs_history_input("Файл виртуальной файловой системы должен иметь расширение .xml", self.SYSTEM)
			return

		if not(self.createdVFS(parameters[1])):
			return

		#================

		try:
			with open(parameters[2], "r") as script:
				command_line = script.readline()
				while command_line:

					command_line = command_line.rstrip()

					self.vfs_history_input(command_line, self.SCRYPT)
					self.vfs_terminal(self.SCRYPT + command_line)
					command_line = script.readline()
		except:
			self.vfs_history_input("Файл стартового скрипта не найден", self.SYSTEM)
			return

	def createdVFS(self, path):

		try:
			tree = ET.parse(path)
		except:
			self.vfs_history_input("Невозможная структура VFS", self.SYSTEM)
			return False


		root = tree.getroot()

		if (root.tag != "directory"):
			self.vfs_history_input("Источник виртуальной файловой системы должен содержать корневую директорию", self.SYSTEM)
			return False

		root_directory = Directory(root.attrib["name"], None)

		self.root_directory = root_directory
		self.current_directory = root_directory

		if not(self.parseXml(root)):
			self.vfs_history_input("Неверная структура или формат данных в VFS-источнике", self.SYSTEM)

			self.root_directory = None
			self.current_directory = None
	
			return False
		return True


	def parseXml(self, directory):

		current_directory = self.current_directory

		for child in directory:

			if (child.tag == "directory"):
				directory = Directory(child.attrib['name'], current_directory)				

				self.current_directory.addChild(directory)

				self.current_directory = directory

				if not(self.parseXml(child)):
					return False

				self.current_directory = current_directory

			elif (child.tag == "file"):

				if child[0].tag != "data":
					return False

				if child.attrib["type"] == "txt":

					file = File(child.attrib["name"], child.attrib["type"], child[0].text, self.current_directory)

				elif child.attrib["type"] in ("bin", "png"):
					
					file = File(child.attrib["name"], child.attrib["type"], child[0].text, self.current_directory)
					#file = File(child.attrib["name"], child.attrib["type"], self.bin_data_decode(child[0].text), self.current_directory)

				else:
					return False

				current_directory.addChild(file)

			else:
				return False
		return True

"""
	def bin_data_decode(self, data):

		base64_bytes = data.encode('ascii') #преобразует обычную строку в байтовую

		message_bytes = base64.b64decode(base64_bytes) #декодирует бинраную строку из формата base64в исходную байтовую строку

		message = message_bytes.decode('ascii') #преобразует байтовую строку в исходную str строку

		return message
"""

def on_activate(app):
	# создаём окно
	window =  VfsTerminal(application = app) #
	#отображаем окно
	window.present()
	
	#создаём приложение и назначаем ему индификатор
app = Gtk.Application(application_id = "com.github.Griboedovich.VFS")
	# присоединяем к сигналу activate функцию on_activated
app.connect("activate", on_activate)
	# запускаем приложение
app.run(None)
	# чтобы выйти необходимо использовать app.quit()
