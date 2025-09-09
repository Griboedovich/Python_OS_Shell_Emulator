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
		pass


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
