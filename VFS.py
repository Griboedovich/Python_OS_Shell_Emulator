import gi # модкль для работы с API связанных с PyGObject который содержит GTK

gi.require_version("Gtk", "4.0") # подключает пространство имён Gtk версии 4
from gi.repository import Gtk


def on_activate(app):
	# создаём и настраиваем  окно
	window = Gtk.ApplicationWindow(application = app) #
	window.set_title ("VFS")
	window.set_default_size (600, 400)
	#отображаем окно
	window.present()
	
	#создаём приложение и назначаем ему индификатор
app = Gtk.Application(application_id = "com.github.Griboedovich.VFS")
	# присоединяем к сигналу activate функцию on_activated
app.connect("activate", on_activate)
	# запускаем приложение
app.run(None)
	# чтобы выйти необходимо использовать app.quit()
