import pygame,math,copy
from inc import events

class Mobile(pygame.sprite.Sprite):
	app = None
	def __init__(self,position,radius=0,app=None):
		pygame.sprite.Sprite.__init__(self)
		object.__setattr__(self, 'position', position)
		object.__setattr__(self, 'radius', radius)
		if self.app == None and app != None: self.app = app
		self.speed = [0,0] # px/s
		self.acceleration = [0,0]
		self.freefall = False
		self.gotoDo = False
		self.moving = False
		self.thickness = 0.995 # air "thickness"
		self.callback = None
		self.plotX = None
		self.plotY = None
		self.state = 1
		# left/top/width/height positions relative to center
		# (x,y),(w,h)
		self.rect = pygame.rect.Rect((0,0),(0,0))
		self.z_index = 0
	def __del__(self):
		pass
	
	# designed to be overloaded when necessary
	def setPosition(self,position):
		object.__setattr__(self, 'position', position)
		self.rect.center = self.position
	def setZIndex(self,z_index):
		object.__setattr__(self, 'z_index', z_index)
	def setRadius(self,radius):
		object.__setattr__(self, 'radius', radius)
	
	def __setattr__(self, name, value):
		if name == 'position':
			self.setPosition(value)
		elif name == 'z_index':
			self.setZIndex(value)
		elif name == 'radius':
			self.setRadius(value)
		else:
			object.__setattr__(self, name, value)

################################################################################
	def dirty(self,rect=None):
		if rect == None: rect = self.rect
		try:
			self.app.addDirty(rect)
		except:
			#print("no appDirty")
			pass

################################################################################

	def config(self,data):
		if type(data) == dict:
			for key in data:
				self.__setattr__(key, data[key])

################################################################################
	
	def notify(self,event):
		if isinstance( event, events.TickEvent ):
			self.update(event.deltat)

	def update(self,deltat):
		pos = copy.copy(self.position)
		rect = copy.copy(self.rect)
		if self.freefall: self.fall(deltat)
		elif self.gotoDo: self.gotoMove(deltat)
		if pos != self.position:
			self.dirty(rect)
			self.dirty()
		
################################################################################

	def fall(self,deltat):
		x, y = self.position
		#
		self.speed[0] += 0 * deltat/1000.
		self.speed[1] += 400 * deltat/1000.
		self.speed[0] *= self.thickness
		self.speed[1] *= self.thickness
		#
		x += self.speed[0] * deltat/1000.
		y += self.speed[1] * deltat/1000.
		#
		if y>768-self.rect.bottom:
			y = 768 -self.rect.bottom
			self.speed[1] = -self.speed[1]
		if x<-self.rect.left:
			x = -self.rect.left
			self.speed[0] = -self.speed[0]
		if x>1024-self.rect.right:
			x = 1024-self.rect.right
			self.speed[0] = -self.speed[0]
		#
		self.position = (x,y)

################################################################################

	def move(self,offset,time=0,callback=None,plotX=None,plotY=None):
		endPos = (self.position[0]+offset[0],self.position[1]+offset[1])
		self.goto(endPos,time,callback,plotX,plotY)

	def goto(self,endPos,time=0,callback=None,plotX=None,plotY=None):
		pos_zero = copy.copy(self.position)
		rect_zero = copy.copy(self.rect)
		if time == 0:
			self.dirty()
			if self.gotoDo:
				self.gotoDo = False
				if self.app:
					self.app.stopAnimation()
					self.app.evManager.UnregisterListener(self,events.TickEvent)
			self.position = endPos
			if callable(callback): callback(self)
			if self.app:
				self.app.requestFrame()
			self.dirty()
		else:
			self.gotoStartPos = self.position
			self.gotoEndPos = endPos
			self.gotoTime = time
			self.gotoProgress = 0
			self.gotoDo = True
			self.moving = True
			self.callback = callback
			if hasattr(plotX, '__call__'):
				self.plotX = plotX
			else:
				self.plotX = self.plotLinearX
			if hasattr(plotY, '__call__'):
				self.plotY = plotY
			else:
				self.plotY = self.plotLinearY
			if self.app:
				self.app.startAnimation()
				self.app.evManager.RegisterListener(self,events.TickEvent)
		#
		if pos_zero != self.position:
			self.dirty(rect_zero)
			self.dirty()

		
	def gotoMove(self,deltat):
		x0,y0 = self.gotoStartPos
		x1,y1 = self.gotoEndPos
		if self.gotoProgress == 0:
			self.gotoProgress += 0.0000001
		else:
			self.gotoProgress += deltat
		if self.gotoTime == 0:
			t = 1
		else:
			t = 1.0*float(self.gotoProgress)/float(self.gotoTime)
		# 
		#print("GOTO MOVE dt:%d gotoProgress:%d gotoTime:%d t:%f"% (deltat,self.gotoProgress, self.gotoTime, t))
		if t >= 1.0:
			# movement ended:
			# place the mobile
			# call the callback to say it's done
			# empty the callbacks to end any possible circular reference
			x,y = x1,y1
			if callable(self.callback): self.callback(self)
			if self.app:
				self.app.stopAnimation()
				self.app.evManager.UnregisterListener(self,events.TickEvent)
			self.gotoDo = False
			self.moving = False
			self.callback = None
			self.plotX = None
			self.plotY = None
		else:
			# move
			x = self.plotX(x0,y0,x1,y1,t)
			y = self.plotY(x0,y0,x1,y1,t)
		#
		self.position = (x,y)
	
	def isMoving(self):
		return self.moving

################################################################################

	def touch(self,pos):
		inrect = self.rect.collidepoint(pos)
		if inrect:
			try:
				mpos = map( (lambda a,b: a-b), pos, self.rect.topleft)
				return self.mask.get_at(mpos) != 0
			except:# IndexError:pass
				return True
		return False

################################################################################
	
	def draw(self,screen,zones=None):
		pass
	def flash(self,time):
		pass

	def plotLinearX(self,x0,y0,x1,y1,t):
		return x0 + (x1-x0) * t
	def plotLinearY(self,x0,y0,x1,y1,t):
		return y0 + (y1-y0) * t

	def plotGravityX(self,x0,y0,x1,y1,t):
		return x0 + math.sin(math.pi*t/2) * (x1-x0)
	def plotGravityY(self,x0,y0,x1,y1,t):
		return y0 + t * t * (y1-y0)

################################################################################

	def remove(self):
		try:
			self.callback = None
			self.plotX = None
			self.plotY = None
			self.app.removeControl(self)
			self.app.removeView(self)
			self.app.evManager.UnregisterListener(self)
		except:
			print("ERROR in Mobile.remove()")
