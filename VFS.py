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
	def getParent(self):
		return self.parent
	def killChild(self, child):
		self.childs.remove(child)

class File():
	def __init__(self, name, f_type, data, parent):
		self.name = name
		self.type = f_type
		self.data = data
		self.parent = parent
	def toString(self):
		return f"{self.name}.{self.type}"
	def getParent(self):
		return self.parent
	def getName(self):
		return self.toString()

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
		self.history_storage = []
		self.last_directory = None

		self.created_history()
		self.created_input()

		self.vfs_buffer.set_text(self.SYSTEM + "WELCOME TO MUSHROOM VFS")

		GLib.timeout_add(30, self.terminal_configuration)

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
		
		#================== for history command ============
		if command != "":
			self.history_storage.append(command_line.replace(sourse, ""))
		#===================================================

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
		elif command == "history":
			self.c_history(command,args_list)
		elif command == "rmdir":
			self.c_rmdir(command, args_list)
		elif command == "touch":
			self.c_touch(command, args_list)
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

		#args = ["-l", "-t", "-a"]	
	
		if self.current_directory is None:
			self.vfs_history_input("Невозможно применить команду ls: отсутсвует VFS", self.SYSTEM)
			return

		if len(args_list) == 0:

			message = ""

			for child in self.current_directory.getChilds():
				message += "\n-" + child.getName()
			self.vfs_history_input(message, self.SYSTEM)
		else:
			self.vfs_history_input("Неожиданные аргументы у команды ls: " + " ".join(args_list[0:]), self.SYSTEM)

	def c_cd(self, command, args_list):

		#args = ["-P", "-L", "-e"]		

		if self.current_directory is None:
			self.vfs_history_input("Невозможно применить команду cd: отсутсвует VFS", self.SYSTEM)
			return

		if len(args_list) == 0:

			self.last_directory = self.current_directory
			self.current_directory = self.root_directory

			# текущая папка - root
			
		elif len(args_list) == 1:
			# проверка на cd -

			if args_list[0] == "-":
				self.current_directory, self.last_directory = self.last_directory, self.current_directory
				return

			path_way = args_list[0].split("/")
			
			intermediate_directory = self.current_directory

			for path_directory in path_way:
				
				if path_directory in [".", ""]:
					continue

				if  path_directory == "..":
					if not (intermediate_directory.getParent() is None):
						intermediate_directory = intermediate_directory.getParent()
					continue

				directory = self.c_cd_search_for_name(path_directory, intermediate_directory.getChilds())

				if directory is None:
					self.vfs_history_input(f"Нет такого каталога: {path_directory}", self.SYSTEM)
					return
				elif not (isinstance(directory, Directory)):
					self.vfs_history_input(f"Это не каталог: {path_directory}", self.SYSTEM)
					return
				else:
					
					intermediate_directory = directory

			self.last_directory = self.current_directory
			self.current_directory = intermediate_directory

		else:
			self.vfs_history_input("Слишком много аргументов", self.SYSTEM)

	def c_cd_search_for_name(self, name, objects):
	
		for element in objects:
			if (element.getName() == name):
				return element
		return None

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

	def c_history(self, command, args_list):
		if len(self.history_storage) == 0:
			self.vfs_history_input("История комманд пуста", self.SYSTEM)
			return

		if len(args_list) == 0:

			message = ""

			for i in range(len(self.history_storage)):
				message += f"\n{str(i+1)}:    {self.history_storage[i]}"
			self.vfs_history_input(message, self.SYSTEM)
		else:
			self.vfs_history_input("Неожиданные аргументы у команды history: " + " ".join(args_list[0:]), self.SYSTEM)

	def c_rmdir(self,command, args_list):
		
		#если не получилось удалить папку то выводится ошибка и след итерация

		if self.current_directory is None:
			self.vfs_history_input("Невозможно применить команду rmdir: отсутсвует VFS", self.SYSTEM)
			return

		if len(args_list) == 0:
			self.vfs_history_input("rmdir: отсутсвуют обязательные аргументы", self.SYSTEM)
			return
		
		for i in args_list:

			is_path_correct, error_message, parent_directory, target = self.c_logic_path_search(i)

			if (not is_path_correct):
				self.vfs_history_input(f"rmdir: не удалось удалить каталог {target}. Ошибка пути: " + error_message, self.SYSTEM)
				continue

			target_object = self.c_cd_search_for_name(target, parent_directory.getChilds())

			if target_object is None:
				self.vfs_history_input(f"rmdir: не удалось удалить каталог {target}: Нет такого каталога" + error_message, self.SYSTEM)
				continue
			elif not (isinstance(target_object, Directory)):
				self.vfs_history_input(f"rmdir: не удалось удалить каталог {target}: Это не каталог" + error_message, self.SYSTEM)
				continue
			elif len(target_object.getChilds()) != 0:
				self.vfs_history_input(f"rmdir: не удалось удалить каталог {target}: Каталог не пуст" + error_message, self.SYSTEM)
				continue
			
			parent_directory.killChild(target_object)

	def c_touch(self,command, args_list):
		
		#если не получилось удалить папку то выводится ошибка и след итерация

		if self.current_directory is None:
			self.vfs_history_input("Невозможно применить команду touch: отсутсвует VFS", self.SYSTEM)
			return

		if len(args_list) == 0:
			self.vfs_history_input("touch: нечего трогать", self.SYSTEM)
			return
		
		for i in args_list:

			is_path_correct, error_message, parent_directory, target = self.c_logic_path_search(i)

			if (not is_path_correct):
				self.vfs_history_input(f"touch: невозможно потрогать {target}. Ошибка пути: " + error_message, self.SYSTEM)
				continue

			target

			point_index = target.rfind(".")

			if point_index == -1:
				file_name = target

				file_type = "nontype"
			else:
				file_name = target[:point_index]

				file_type = target[point_index + 1:]

			target_object = File(file_name, file_type, "", parent_directory)			

			parent_directory.addChild(target_object)

	def c_logic_path_search(self, path):
		path_way = path.split("/")
		
		error_message = ""		

		i = 0

		while i < len(path_way):
			if path_way[i] in [".", ""]:
				path_way.pop(i)
			else:
				i += 1
			
		target = path_way[-1]
		path_way = path_way[ : -1]

		intermediate_directory = self.current_directory

		for path_directory in path_way:
			
			if  path_directory == "..":
				if not (intermediate_directory.getParent() is None):
					intermediate_directory = intermediate_directory.getParent()
				continue

			directory = self.c_cd_search_for_name(path_directory, intermediate_directory.getChilds())

			if directory is None:
				error_message = f"нет такого каталога: {path_directory}"
				return (False, error_message,  None, target)
			elif not (isinstance(directory, Directory)):
				error_message = f"это не каталог: {path_directory}" 
				return (False, error_message,  None, target)
			else:
					
				intermediate_directory = directory

		return (True, error_message, intermediate_directory, target)


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
