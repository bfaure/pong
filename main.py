# python 2.7
from __future__ import print_function
import os
import sys
import time
import random
from copy import deepcopy, copy
from time import sleep

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

pyqt_app = ""

class cell(object):
	def __init__(self):
		self.value = 0
		self.render_coordinate = [None,None]
	def state(self):
		return self.value
	def set_occupied(self):
		self.value = 1
	def set_free(self):
		self.value = 0
	def set_target(self):
		self.value = 2


class frame_manager(QThread):
	update_grid = pyqtSignal()

	def __init__(self,parent=None):
		QThread.__init__(self,parent)
		self.connect(self,SIGNAL("update_grid()"),parent.repaint)

	def run(self):
		refresh_period = 0.2
		while True:
			if self.stop: break
			self.update_grid.emit()
			sleep(refresh_period)

# UI element (widget) that represents the interface with the grid
class eight_neighbor_grid(QWidget):
	end_game = pyqtSignal()

	def __init__(self,num_cols=40,num_rows=40,pyqt_app=None,parent=None):
		# constructor, pass the number of cols and rows
		super(eight_neighbor_grid,self).__init__()
		self.parent	  = parent
		self.connect(self,SIGNAL("end_game()"),parent.game_over)
		self.num_cols = num_cols # width of the board
		self.num_rows = num_rows # height of the board
		self.pyqt_app = pyqt_app # allows this class to call parent functions
		self.init_ui() # initialize a bunch of class instance variables

	def init_cells(self):
		self.cells = []
		for _ in range(self.num_rows):
			row = []
			for _ in range(self.num_cols):
				cur_cell = cell()
				row.append(cur_cell)
			self.cells.append(row)

	def init_ui(self):
		# initialize ui elements
		self.grid_line_color = [0,0,0]
		self.free_color = [128,128,128]
		self.occupied_color = [0,128,255]
		self.blocked_cell_color = [0,0,0]
		self.target_color=[124,252,0]
		self.last_direction = "right"
		self.current_location = None
		self.game_over = False

		self.cells_visited=[]
		self.tail_length=10

		self.init_cells()

		self.frame_updater = frame_manager(self)
		self.frame_updater.stop=False
		self.frame_updater.start()

	def paintEvent(self,e):
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

		if self.game_over: 
			self.user_health+=-1
			self.game_over = False
			self.end_game.emit()

	def drawWidget(self,qp):
		size = self.size()
		height = size.height()
		width = size.width()

		self.horizontal_step = int(round(width/self.num_cols))
		self.vertical_step = int(round(height/self.num_rows))

		grid_height = self.vertical_step*self.num_rows
		grid_width = self.horizontal_step*self.num_cols

		qp.setBrush(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))
		qp.setPen(Qt.NoPen)

		for y in range(self.num_rows):
			for x in range(self.num_cols):
				cell_state = self.get_cell_state(x,y)

				if cell_state==1: # player in current location
					qp.setBrush(QColor(self.occupied_color[0],self.occupied_color[1],self.occupied_color[2]))
					self.current_location = [x,y]

				elif cell_state==2: # target in current location
					qp.setBrush(QColor(self.target_color[0],self.target_color[1],self.target_color[2]))

				elif cell_state==0: # current location is free
					qp.setBrush(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))

				if [x,y] in self.cells_visited[:self.tail_length]:
					qp.setBrush(QColor(self.occupied_color[0],self.occupied_color[1],self.occupied_color[2]))

				x_start = x*self.horizontal_step
				y_start = y*self.vertical_step
				qp.drawRect(x_start,y_start,self.horizontal_step,self.vertical_step)

				self.cells[y][x].render_coordinate = [x_start,y_start]

	def get_cell_state(self,x,y):
		return self.cells[y][x].state()

	def get_open_cell(self):
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				if self.cells[y][x].state()==0:
					return [x,y]
		return [-1,-1]

	def get_start_cell(self):
		x=random.randint(1,self.num_cols-1)
		y=random.randint(1,self.num_rows-1)
		self.cells[y][x].set_occupied()

	def get_target_cell(self):
		while True:
			x=random.randint(1,self.num_cols-1)
			y=random.randint(1,self.num_rows-1)
			if self.get_cell_state(x,y)==0: break
		self.cells[y][x].set_target()	

	def get_cell_attrib(self,attrib=1):
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				if self.cells[y][x].state()==attrib:
					return [x,y]
		return [-1,-1]

	def move(self,action="none"):
		self.last_direction = action

		cur_x,cur_y = self.get_cell_attrib(attrib=1)
		if cur_x==-1 and cur_y==-1:
			print("ERROR: move() could not find current cell!")
			return [-1,-1]

		x,y = cur_x,cur_y

		if action=="left": x+=-1
		if action=="right": x+=1
		if action=="up": y+=-1
		if action=="down": y+=1

		if x==-1 or x==self.num_cols: 
			return [cur_x,cur_y]
		if y==-1 or y==self.num_rows: 
			return [cur_x,cur_y]

		self.cells_visited=[[x,y]]+self.cells_visited

		self.cells[cur_y][cur_x].set_free()
		self.cells[y][x].set_occupied()
		self.current_location = [x,y]
		return [x,y]

	def get_opposite_direction(self,direction):
		if direction=="left": return "right"
		if direction=="right": return "left"
		if direction=="up": return "down"
		if direction=="down": return "up"
		return "none"

	def set_current_location(self,location_descriptor):
		if location_descriptor=="opposite":
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					if self.cells[y][x].state()==1:
						self.cells[y][x].set_free()
			self.current_location = [self.num_cols-1,self.num_rows-1]
			self.cells[self.num_rows-1][self.num_cols-1].set_occupied()
			return [self.num_cols-1,self.num_rows-1]
		if location_descriptor=="standard":
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					if self.cells[y][x].state()==1:
						self.cells[y][x].set_free()
			self.current_location = [0,0]
			self.cells[0][0].set_occupied()
			return [0,0]


class main_window(QWidget):

	def __init__(self,parent=None):
		super(main_window,self).__init__()
		self.num_cols = 50
		self.num_rows = 30
		self.init_ui()
		self.start_character()
		self.start_target()

	def init_ui(self):
		self.setWindowTitle('Snake')
		self.menu_selection_sound = QSound("resources/sounds/341695__projectsu012__coins-1.wav")
		self.dead_sound = QSound("resources/sounds/350985__cabled-mess__lose-c-02.wav")
		self.win_sound = QSound("resources/sounds/126422__cabeeno-rossley__level-up.wav")
		
		self.min_width = 625
		self.min_height = 425

		self.layout = QVBoxLayout(self)
		self.grid = eight_neighbor_grid(num_cols=self.num_cols,num_rows=self.num_rows,parent=self)

		if sys.platform in ["apple","Apple","darwin","Darwin"]:
			self.min_height = 470
			self.min_width = 675

		if sys.platform in ["linux","linux32","win32"]: 
			self.layout.addSpacing(25)
			self.min_height+=25

		self.layout.addWidget(self.grid)

		self.toolbar = QMenuBar(self)
		self.toolbar.setFixedWidth(self.min_width)

		file_menu = self.toolbar.addMenu("File")
		file_menu.addAction("Quit",self.quit,QKeySequence("Ctrl+Q"))

		self.setFixedWidth(self.min_width)
		self.setFixedHeight(self.min_height)
		self.show()

	def quit(self):
		self.grid.frame_updater.stop=True
		sys.exit(1)

	def closeEvent(self,e):
		self.quit()

	def start_character(self):
		self.grid.get_start_cell()

	def start_target(self):
		self.grid.get_target_cell()

	def keyPressEvent(self,e):
		if e.isAutoRepeat(): return

		action = None
		if e.key() == Qt.Key_Left: action="left"
		if e.key() == Qt.Key_Right: action="right"
		if e.key() == Qt.Key_Up: action="up"
		if e.key() == Qt.Key_Down: action="down"

		if action!=None:
			new_direction = self.grid.move(action)

	def game_over(self):
		user_health = self.grid.user_health
		if user_health<=0:
			self.dead_sound.play()
			self.grid.set_current_location("opposite")
			pyqt_app.processEvents()
			if self.opponent_ip!=None:
				self.grid.opponent_move(0,0)
				sender = sender_thread()
				sender.host = self.opponent_ip
				sender.message = "restart| "
				sender.is_done = False 
				sender.start()
				self.sender_threads.append(sender)
			self.grid.init_blocked_cells()
			self.grid.setEnabled(False)
			self.set_health(10)
		else:
			self.set_health(user_health)

def main():
	global pyqt_app
	pyqt_app = QApplication(sys.argv)
	_ = main_window()
	sys.exit(pyqt_app.exec_())

if __name__ == '__main__':
	main()