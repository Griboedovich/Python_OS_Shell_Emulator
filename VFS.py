import gi # модкль для работы с API связанных с PyGObject который содержит GTK

gi.require_version("Gtk", "4.0") # подключает пространство имён Gtk версии 4
from gi.repository import Gtk, GLib

class VfsTerminal(Gtk.ApplicationWindow):
	def __init__(self, **kargs):
		super().__init__(**kargs, title = "VFS")
		self.set_default_size (600, 400)

		self.vfs_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)
		self.set_child(self.vfs_box)

		self.SYSTEM = "system > "
		self.USER = "user > "

		self.created_history()
		self.created_input()

		self.vfs_buffer.set_text(self.SYSTEM + "WELCOME TO MUSHROOM VFS")

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

		command_words = command_line.split()

		#print(command_words)

		if (len(command_words) < 2 or (( command_words[0] + " " + command_words[1] + " " ) != self.USER)):
			self.vfs_history_input("Неккоректный источник", self.SYSTEM)
			return
		
		sourse = command_words[:2]
		command_words.pop(0)
		command_words.pop(0)
		
		if len(command_words) == 0: return

		command_lenght = len(command_words)

		if command_words[0] == "exit":
			self.c_exit(command_words, command_lenght)
		elif command_words[0] == "ls":
			self.c_ls(command_words, command_lenght)
		elif command_words[0] == "cd":
			self.c_cd(command_words, command_lenght)
		else:
				self.vfs_history_input("Неизвестная команда: " + command_words[0], self.SYSTEM)

	def c_exit(self, command_list, command_lenght):
		
			if command_lenght == 1:
				self.get_application().quit()
			else:
				self.vfs_history_input("Неожиданные аргументы у команды exit: " + " ".join(command_list[1:]), self.SYSTEM)

	def c_ls(self, command_list, command_lenght):

		args = ["-l", "-t", "-a"]		

		if command_lenght == 1:
			self.vfs_history_input("ls", self.SYSTEM)
		else:	
			result_line = "ls "
			error_line = "Неверные аргументы у команды ls:"
			error_check = False
			for i in command_list[1:]:
				if i in args:
					result_line += " " + i
				else:
					error_check = True
					error_line += " | " + i
			if error_check:
				self.vfs_history_input(error_line + " |", self.SYSTEM)
			else:
				self.vfs_history_input(result_line, self.SYSTEM)

	def c_cd(self, command_list, command_lenght):

		args = ["-P", "-L", "-e"]		

		if command_lenght == 1:
			self.vfs_history_input("cd", self.SYSTEM)
		else:	
			result_line = ""
			file_line = ""
			args_line = "cd "
			error_line = "Неверные аргументы у команды cd:"
			error_check = False
			for i in command_list[1:]:
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
					file_line = self.arg_parser(i)
					if file_line == '"error"':
						error_line = "| Фокусы с кавычками запрещены"
						error_check = True
						break
					else:
						file_line = " ---open--> " + file_line
			if error_check:
				self.vfs_history_input(error_line + " |", self.SYSTEM)
			else:
				result_line = args_line + file_line
				self.vfs_history_input(result_line, self.SYSTEM)

	def arg_parser(self, argument):

		valid_list = []

		if (argument.count("'") % 2) != 0:
			return "error"
		if (argument.count('"') % 2) != 0:
			return "error"

		for i in argument:
			if i == "'" or i == '"':
				if len(valid_list) == 0 or i != valid_list[len(valid_list) - 1]:
					valid_list.append(i)
				else:
					valid_list.pop()
		if len(valid_list) != 0:
			return "error"
		argument = argument.replace("'", "")
		argument = argument.replace('"', '')
		argument = argument.replace(" ", "_")

		return argument

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
