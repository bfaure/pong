# python 2.7
import os
import sys
import time
import random
from time import sleep

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Cell:
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


class FrameManager(QThread):
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

class Grid(QWidget):

	def __init__(self,num_cols,num_rows,parent):
		super(Grid,self).__init__()
		self.parent	  = parent # allows this class to manipulate parent
		self.num_cols = num_cols # width of the board
		self.num_rows = num_rows # height of the board
		self.init_ui() # initialize a bunch of class instance variables

	def init_cells(self):
		self.cells = []
		for _ in range(self.num_rows):
			row = []
			for _ in range(self.num_cols):
				cur_cell = Cell()
				row.append(cur_cell)
			self.cells.append(row)

	def init_ui(self):
		self.free_color = [128,128,128] # color of open cells
		self.occupied_color = [0,128,255] # color of snake
		self.target_color=[124,252,0] # color of targets
		self.last_direction = None # one of ['left','right','up','down']
		self.current_location = None # [x,y] coords

		self.hi_score=0 # highest score of current session
		self.points=0 # current score
		self.cells_visited=[] # path of visited locations [x,y]'s
		self.tail_length=0 # based on current score

		self.init_cells() # create all cell objects

		self.frame_updater = FrameManager(self) # to handle refresh rate
		self.frame_updater.stop=False 
		self.frame_updater.start() 

	def paintEvent(self,e):
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def new_game(self):
		print 'Game Over! Your score was %d'%self.points
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
		size   = self.size() # size of current window
		height = size.height()
		width  = size.width()

		horizontal_step = int(round(width/self.num_cols))
		vertical_step   = int(round(height/self.num_rows))

		grid_height = vertical_step*self.num_rows
		grid_width  = horizontal_step*self.num_cols

		qp.setPen(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))

		if self.last_direction!=None:
			self.move(self.last_direction)

		last_brush=None
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				cell_state=self.cells[y][x].state()

				if cell_state==1 or [x,y] in self.cells_visited[:self.tail_length]: # player in current location
					if last_brush!='user':
						qp.setBrush(QColor(self.occupied_color[0],self.occupied_color[1],self.occupied_color[2]))
					last_brush='user'

				elif cell_state==2: # target in current location
					if last_brush!='target':
						qp.setBrush(QColor(self.target_color[0],self.target_color[1],self.target_color[2]))
					last_brush='target'

				else: # current location is free
					if last_brush!='free':
						qp.setBrush(QColor(self.free_color[0],self.free_color[1],self.free_color[2]))
					last_brush='free'

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
		self.last_direction=action
		x,y=self.current_location
		self.cells[y][x].set_free()
		if self.last_direction=="right":  x+=1
		elif self.last_direction=="left": x+=-1
		elif self.last_direction=="up":   y+=-1
		elif self.last_direction=="down": y+=1

		if x<0 or x>=self.num_cols: return self.new_game()
		if y<0 or y>=self.num_rows: return self.new_game()
		if [x,y] in self.cells_visited[:self.tail_length]:
			return self.new_game()

		self.current_location=[x,y]
		if self.cells[y][x].value==2:
			self.parent.score_sound.play()
			self.tail_length+=4
			self.get_target_cell()
			self.points+=1
			self.parent.setWindowTitle('Snake - Score: %d - High: %d'%(self.points,self.hi_score))
		self.cells[y][x].set_occupied()
		self.cells_visited=[[x,y]]+self.cells_visited
		self.cells_visited=self.cells_visited[:self.tail_length]


class MainWindow(QWidget):

	def __init__(self,parent=None):
		super(MainWindow,self).__init__()
		self.num_cols = 40
		self.num_rows = 25
		self.key_dict={Qt.Key_Left:'left',Qt.Key_Right:'right',Qt.Key_Up:'up',Qt.Key_Down:'down',Qt.Key_P:'pause'}
		self.init_ui() # create grid
		self.grid.get_start_cell() # initialize player location
		self.grid.get_target_cell() # initialize first target

	def init_ui(self):
		self.setWindowTitle('Snake - Score: 0 - High: 0')
		self.setWindowIcon(QIcon('resources/icons/snake_icon.png'))
		self.dead_sound  = QSound("resources/sounds/350985__cabled-mess__lose-c-02.wav")
		self.score_sound = QSound("resources/sounds/126422__cabeeno-rossley__level-up.wav")
		
		self.min_width  = 625
		self.min_height = 425

		self.layout = QVBoxLayout(self)
		self.grid   = Grid(num_cols=self.num_cols,num_rows=self.num_rows,parent=self)

		if sys.platform in ["apple","Apple","darwin","Darwin"]:
			self.min_height = 470
			self.min_width  = 675

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

	def keyPressEvent(self,e):
		if e.isAutoRepeat(): return

		try:    action=self.key_dict[e.key()]
		except: return

		if action=="pause":
			if self.grid.frame_updater.pause==True:
				self.grid.frame_updater.pause=False
			else:
				self.grid.frame_updater.pause=True
		else:
			self.grid.move(action)

	def resizeEvent(self,e):
		size   = self.size() # size of current window
		width  = size.width()
		self.toolbar.setFixedWidth(width) # resize toolbar to fit new window size

def main():
	pyqt_app = QApplication(sys.argv)
	_ = MainWindow()
	sys.exit(pyqt_app.exec_())

if __name__ == '__main__':
	main()