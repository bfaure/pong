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
		self.pause=False
		self.connect(self,SIGNAL("update_grid()"),parent.repaint)

	def run(self):
		refresh_period = 0.08
		while True:
			if self.stop: break
			if not self.pause: self.update_grid.emit()
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
		self.last_direction = None
		self.current_location = None


		self.hi_score=0
		self.points_to_win=20
		self.points=0
		self.cells_visited=[]
		self.tail_length=0

		self.init_cells()

		self.frame_updater = frame_manager(self)
		self.frame_updater.stop=False
		self.frame_updater.start()

	def paintEvent(self,e):
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def move_player(self):
		x,y=self.current_location
		self.cells[y][x].set_free()
		if self.last_direction=="right":
			x+=1
		if self.last_direction=="left":
			x+=-1
		if self.last_direction=="up":
			y+=-1
		if self.last_direction=="down":
			y+=1

		if x<0 or x>=self.num_cols:
			return self.new_game()
		if y<0 or y>=self.num_rows:
			return self.new_game()
		if [x,y] in self.cells_visited[:self.tail_length]:
			return self.new_game()

		self.current_location=[x,y]
		if self.cells[y][x].value==2:
			self.parent.win_sound.play()
			self.tail_length+=4
			self.get_target_cell()
			self.points+=1
			self.parent.setWindowTitle('Snake - Score: %d - High: %d'%(self.points,self.hi_score))
		self.cells[y][x].set_occupied()
		self.cells_visited=[[x,y]]+self.cells_visited

	def new_game(self):
		self.parent.dead_sound.play()
		self.cells_visited=[]
		self.last_direction=None
		self.tail_length=0
		if self.points>self.hi_score: self.hi_score=self.points
		self.points=0
		self.parent.setWindowTitle('Snake - Score: %d - High: %d'%(self.points,self.hi_score))
		self.init_cells()
		self.get_start_cell()
		self.get_target_cell()

	def drawWidget(self,qp):
		size = self.size() # size of current window
		height = size.height()
		width = size.width()

		horizontal_step = int(round(width/self.num_cols))
		vertical_step = int(round(height/self.num_rows))

		grid_height = vertical_step*self.num_rows
		grid_width = horizontal_step*self.num_cols

		qp.setBrush(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))
		qp.setPen(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))

		if self.last_direction!=None:
			self.move_player()

		for y in range(self.num_rows):
			for x in range(self.num_cols):
				cell_state=self.cells[y][x].state()

				if cell_state==1 or [x,y] in self.cells_visited[:self.tail_length]: # player in current location
					qp.setBrush(QColor(self.occupied_color[0],self.occupied_color[1],self.occupied_color[2]))

				elif cell_state==2: # target in current location
					qp.setBrush(QColor(self.target_color[0],self.target_color[1],self.target_color[2]))

				else: # current location is free
					qp.setBrush(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))

				x_start = x*horizontal_step
				y_start = y*vertical_step
				qp.drawRect(x_start,y_start,horizontal_step,vertical_step)

	def get_start_cell(self):
		x=random.randint(1,self.num_cols-1)
		y=random.randint(1,self.num_rows-1)
		self.current_location=[x,y]
		self.cells[y][x].set_occupied()

	def get_target_cell(self):
		while True:
			x=random.randint(1,self.num_cols-1)
			y=random.randint(1,self.num_rows-1)
			if self.cells[y][x].state()==0 and [x,y] not in self.cells_visited[:self.tail_length]:
				break
		self.cells[y][x].set_target()	

	def move(self,action="none"):
		self.last_direction = action

		cur_x,cur_y = self.current_location
		if cur_x==-1 and cur_y==-1:
			print("ERROR: move() could not find current cell!")
			return [-1,-1]

		x,y = cur_x,cur_y

		if action=="left": x+=-1
		if action=="right": x+=1
		if action=="up": y+=-1
		if action=="down": y+=1

		if x<0 or x>=self.num_cols:
			return self.new_game()
		if y<0 or y>=self.num_rows:
			return self.new_game()
		if [x,y] in self.cells_visited[:self.tail_length]:
			return self.new_game()

		if self.cells[y][x].value==2:
			self.parent.win_sound.play()
			self.tail_length+=4
			self.get_target_cell()
			self.points+=1
			self.parent.setWindowTitle('Snake - Score: %d - High: %d'%(self.points,self.hi_score))

		self.cells_visited=[[x,y]]+self.cells_visited
		self.cells_visited=self.cells_visited[:self.tail_length]

		self.cells[cur_y][cur_x].set_free()
		self.cells[y][x].set_occupied()
		self.current_location = [x,y]
		return [x,y]


class main_window(QWidget):

	def __init__(self,parent=None):
		super(main_window,self).__init__()
		self.num_cols = 40
		self.num_rows = 25
		self.init_ui()
		self.start_character()
		self.start_target()

	def init_ui(self):
		self.setWindowTitle('Snake - Score: 0 - High: 0')
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

		self.resize(self.min_width,self.min_height)
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
		if e.key() == Qt.Key_P: action="pause"

		if action=="pause":
			if self.grid.frame_updater.pause==True:
				self.grid.frame_updater.pause=False
			else:
				self.grid.frame_updater.pause=True

		elif action!=None:
			new_direction = self.grid.move(action)

	def game_over(self):
		print ("game over")

def main():
	global pyqt_app
	pyqt_app = QApplication(sys.argv)
	_ = main_window()
	sys.exit(pyqt_app.exec_())

if __name__ == '__main__':
	main()