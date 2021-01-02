#SECURITY NOTE: anything in here can be created simply by sending the 
# class name over the network.  This is a potential vulnerability
# I wouldn't suggest letting any of these classes DO anything, especially
# things like file system access, or allocating huge amounts of memory

import pygame,time,weakref
WAITER_EVENT = pygame.USEREVENT + 1
SOUND_EVENT = pygame.USEREVENT + 2
SLOW_TEMPO_EVENT = pygame.USEREVENT + 3
PEVENTS = {
	pygame.QUIT: 'QUIT',
	pygame.ACTIVEEVENT: 'ACTIVEEVENT',
	pygame.KEYDOWN: 'KEYDOWN',
	pygame.KEYUP: 'KEYUP',
	pygame.MOUSEMOTION: 'MOUSEMOTION',
	pygame.MOUSEBUTTONUP: 'MOUSEBUTTONUP',
	pygame.MOUSEBUTTONDOWN: 'MOUSEBUTTONDOWN',
	pygame.JOYAXISMOTION: 'JOYAXISMOTION',
	pygame.JOYBALLMOTION: 'JOYBALLMOTION',
	pygame.JOYHATMOTION: 'JOYHATMOTION',
	pygame.JOYBUTTONUP: 'JOYBUTTONUP',
	pygame.JOYBUTTONDOWN: 'JOYBUTTONDOWN',
	pygame.VIDEORESIZE: 'VIDEORESIZE',
	pygame.VIDEOEXPOSE: 'VIDEOEXPOSE',
	pygame.USEREVENT: 'USEREVENT',
	WAITER_EVENT: 'WAITER_EVENT',
	SOUND_EVENT: 'SOUND_EVENT',
	SLOW_TEMPO_EVENT: 'SLOW_TEMPO_EVENT'
}

class Event:
	"""this is a superclass for any events that might be generated by an
	object and sent to the EventManager"""
	def __init__(self,sender):
		self.type = self.__class__
		self.prec_time = time.time()
		try:
			self._sender = weakref.ref(sender)
		except:
			self._sender = sender
	def __str__(self):
		tt = self.type
		if tt in PEVENTS: tt = PEVENTS[tt]
		elif type(tt) == int: tt = repr(tt)
		else: tt = self.__class__.__name__
		return '<%s %s %s>' % (tt,id(self),self.__class__.__name__)
	def sender(self):
		if isinstance(self._sender,weakref.ref):
			return self._sender()
		return self._sender

class WrapperEvent(Event):
	def __init__(self,base_event,prec_time):
		Event.__init__(self,None)
		self.base_event = base_event
		self.type = base_event.type
		self.prec_time = prec_time
	def __getattr__(self,name):
		return getattr(self.base_event,name)

class TickEvent(Event):
	def __init__(self,sender,deltat):
		Event.__init__(self,sender)
		self.deltat = deltat

class WaiterEvent(Event):
	def __init__(self,sender,time):
		Event.__init__(self,sender)
		self.time = time

class SecondEvent(Event):
	def __init__(self,sender):
		Event.__init__(self,sender)

class QuitEvent(Event):
	def __init__(self,sender):
		Event.__init__(self,sender)

class FatalEvent(Event):
	def __init__(self,sender,*args):
		Event.__init__(self,sender)
		self.args = args

class PointEndMoveEvent(Event):
	def __init__(self,sender,point=None):
		Event.__init__(self,sender)
		self.point = point

class ControllerFinishedEvent(Event):
	"""an event sent by a controller when he is in his final state.
	parent controllers (if any) are supposed to catch it, verify the sender's identity and do whatever they need to do about it (like process some result available in the controller object or start a new controller or whatever)"""
	def __init__(self,sender):
		Event.__init__(self,sender)

class LogSomeDataEvent(Event):
	"""this event carries data that should be logged about the current experiment.
	The data is the data to log, with additionnal information provided in the context dictionary, to help know the type the data, and where it comes from"""
	def __init__(self,sender,keys,context):
		Event.__init__(self,sender)
		self.keys = keys
		self.context = context

class ContinueArrowClicked(Event):
	"""the continue arrow has been clicked ! weeeeeee"""
	def __init__(self,sender):
		Event.__init__(self,sender)