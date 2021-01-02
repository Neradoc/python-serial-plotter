import pygame,math,copy
from views import mobile

class TextMobile(mobile.Mobile):
	def __init__(self,position, text, color=None, background=None, border=None, corner=0, fontsize=38, alignement="center", id="", fontname=None, pressedColor=None, pressedBackground=None):
		mobile.Mobile.__init__(self,position)
		self.text = text
		self.alignement = alignement
		# text color
		if isinstance(color,pygame.Color):
			self.color = color
		else:
			self.color = pygame.Color("#000000FF")
		# background color
		if isinstance(background,pygame.Color):
			self.background = background
		else:
			self.background = None
		# border color
		if isinstance(border,pygame.Color):
			self.border = border
		else:
			self.border = None
		# highlight color when pressed
		if isinstance(pressedColor,pygame.Color):
			self.pressedColor = pressedColor
		else:
			self.pressedColor = pygame.Color("white")
		# highlight background color when pressed
		if isinstance(pressedBackground,pygame.Color):
			self.pressedBackground = pressedBackground
		else:
			self.pressedBackground = pygame.Color(50,50,50)
		# corner roundness (0)
		self.corner = corner
		# font name
		if fontname == None:
			self.font = pygame.font.Font("fonts/freesansbold.ttf",fontsize)
		else:
			self.font = pygame.font.Font(font,fontsize)
		# identifier for comparison
		self.id = id
		#
		self.visible = True
		self.pressed = False
		#
		self.redraw()
	
	def redraw(self):
		images = []
		width = 0
		height = 0
		textes = self.text.split("\n")
		if self.pressed:
			color = self.pressedColor
			background = self.pressedBackground
		else:
			color = self.color
			background = self.background
		for tt in textes:
			image = self.font.render(tt, True, color)
			images += [image]
			irect = copy.copy(image.get_rect())
			width = max(irect.width,width)
			height += irect.height
		self.image = pygame.Surface((width+16,height+12))
		self.image = self.image.convert_alpha()
		self.image.fill(pygame.Color("#FFFFFF00"))
		self.rect.size = (width+16,height+12)
		#
		if background != None:
			rect = copy.copy(self.rect)
			rect.topleft = (2,2)
			rect.width -= 4
			rect.height -= 4
			pygame.draw.rect(self.image, background, rect, border_radius=self.corner)
		#
		height = 6
		for ii in images:
			rect = copy.copy(ii.get_rect())
			rect.top = height
			rect.centerx = self.rect.width/2
			self.image.blit(ii,rect)
			height += rect.height
		#
		if self.border != None:
			rect = copy.copy(self.rect)
			rect.topleft = (2,2)
			rect.width -= 4
			rect.height -= 4
			pygame.draw.rect(self.image, self.border, rect, 2, border_radius=self.corner)
		#
		if self.alignement == "topleft":
			self.rect.topleft = self.position
		elif self.alignement == "topright":
			self.rect.topright = self.position
		else:
			self.rect.center = self.position
		self.dirty()
	
	def onPressed(self):
		self.pressed = True
		self.redraw()
	
	def endPressed(self):
		self.pressed = False
		self.redraw()

	def draw(self,screen,zones=None):
		screen.blit(self.image,self.rect)
