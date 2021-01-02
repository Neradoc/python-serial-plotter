import serial, re, math, sys, time
import pygame

test_port = "/dev/tty.usbmodem7CDFA103B7B41"

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('port', type=str, help="Serial port of the board", default=test_port, nargs='?')
args = parser.parse_args()

def wheel(wheel_pos):
	wheel_pos = wheel_pos % 255
	if wheel_pos < 85:
		return 255 - wheel_pos * 3, 0, wheel_pos * 3
	elif wheel_pos < 170:
		wheel_pos -= 85
		return 0, wheel_pos * 3, 255 - wheel_pos * 3
	else:
		wheel_pos -= 170
		return wheel_pos * 3, 255 - wheel_pos * 3, 0

# wheel(90*i) for i in range(0,10)]
colors = [pygame.Color(c) for c in [
	(0xFF,0x26,0x00), #FF2600
	(0x4F,0x8F,0x00), #4F8F00
	(0x00,0x96,0xFF), #0096FF
	(0xFF,0xFB,0x00), #FFFB00
	(0xD7,0x83,0xFF), #D783FF
	(0xFF,0x93,0x00), #FF9300
	(0x00,0x91,0x93), #009193
	(0x94,0x17,0x51), #941751
	(0x94,0x52,0x00), #945200
	(0x73,0xFC,0xD6), #73FCD6
]]
COLOR_BLACK = pygame.Color(0,0,0)
COLOR_WHITE = pygame.Color(255,255,255)

screen_size = [1024,800]
gleft = 0
gtop = 24 + 8
gbottom = 5
gwidth = 1024
gheight = 800 - (gtop+gbottom)
backgroundColor = COLOR_WHITE
axesColor = pygame.Color(100,100,100)
borderColor = pygame.Color(180,180,180)
axesMargin = 0.02 # percentage margin above and below graphs when centered

######################################################################
# startup and configure pygame and other stuff
######################################################################
screen_flags = pygame.HWSURFACE | pygame.DOUBLEBUF
#screen_flags |= pygame.FULLSCREEN

pygame.init()
pygame.display.init()
window = pygame.display.set_mode(screen_size,screen_flags)
screen = pygame.display.get_surface()

channel = None # created (and recreated as necessary) in the loop

######################################################################
# helpers
######################################################################

# math stuff
def calcpos(val,vmin,vmax):
	height = vmax-vmin
	if height == 0:
		return math.floor(gbottom+gheight/2)
	calc = math.floor((val - vmin) * gheight/height) + gbottom
	#print("| %9.1f < %9.1f < %9.1f ==> %9.1f |" % (vmin, val, vmax, calc))
	return screen_size[1] - calc

######################################################################
# UI stuff
######################################################################
# font = "fonts/AurulentSansMono-Regular.otf"
from views import textmobile
listButtons = [
	textmobile.TextMobile((0,0), "Center", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="c"),
	textmobile.TextMobile((0,0), "Axes Communs", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="m"),
]
for x in range(1,10):
	listButtons.append(textmobile.TextMobile((0,0), str(x), background=colors[x-1], border=borderColor, fontsize=16, corner=8, id=str(x)))
#
listButtons.append(textmobile.TextMobile((0,0), "-", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="-"))
listButtons.append(textmobile.TextMobile((0,0), "+", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="+"))
#
listButtons.append(textmobile.TextMobile((0,0), "ctrl-D", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="ctrl-d"))
listButtons.append(textmobile.TextMobile((0,0), "ctrl-C", background=COLOR_WHITE, border=borderColor, fontsize=16, corner=8, id="ctrl-c"))
#
def reDrawButtons():
	bTop = 0
	bLeft = 4
	for butt in listButtons:
		if not butt.visible: continue
		butt.rect.topleft = (bLeft,bTop)
		butt.draw(screen)
		bLeft = bLeft + 4 + butt.rect.width

######################################################################
# loop stuff
######################################################################
progress = 0
previous = None
points = [None] * gwidth
backlog = []
valMin = [None]
valMax = [None]
displayOn = [True]
lineWidth = 1
pauseGraph = False
axesCentered = False
axesCommon = False
blankDraw = False

######################################################################
# initial draw
######################################################################
pygame.draw.rect(screen,backgroundColor,pygame.Rect(0,0,screen_size[0],screen_size[1]))
pygame.draw.rect(screen,backgroundColor,pygame.Rect(gleft, gtop-1, gwidth+2, gheight+2))
pygame.draw.rect(screen,axesColor,pygame.Rect(gleft, gtop-1, gwidth+2, gheight+2), width=1)
reDrawButtons()

print("Running")
running = True
while running:
	# display stuff
	pygame.display.flip()
	######################################################################
	# event loop #########################################################
	######################################################################
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN:
			if event.unicode == " ":
				pauseGraph = not pauseGraph
			if event.unicode == "r":
				points = [None] * gwidth
			if event.unicode == "-":
				lineWidth = max(1,lineWidth-1)
			if event.unicode == "+":
				lineWidth = min(20,lineWidth+1)
			if event.unicode == "m":
				axesCommon = not axesCommon
			if event.unicode == "c":
				axesCentered = not axesCentered
			if event.unicode == "b":
				blankDraw = not blankDraw
			if event.unicode in ["1","2","3","4","5","6","7","8","9"]:
				index = int(event.unicode)-1
				if index < len(displayOn):
					displayOn[index] = not displayOn[index]
		elif event.type == pygame.MOUSEBUTTONDOWN:
			for butt in listButtons:
				if butt.rect.collidepoint(event.pos) and event.button == 1:
					butt.onPressed()
		elif event.type == pygame.MOUSEBUTTONUP:
			for butt in listButtons:
				if butt.rect.collidepoint(event.pos) and event.button == 1:
					if butt.id == "c":
						axesCentered = not axesCentered
					elif butt.id == "m":
						axesCommon = not axesCommon
					elif butt.id in ["1","2","3","4","5","6","7","8","9"]:
						index = int(butt.id)-1
						if index < len(displayOn):
							displayOn[index] = not displayOn[index]
					elif butt.id == "ctrl-c":
						if channel:
							channel.write(b'\x03')
					elif butt.id == "ctrl-d":
						if channel:
							channel.write(b'\x04')
					elif butt.id == "-":
						lineWidth = max(1,lineWidth-1)
					elif butt.id == "+":
						lineWidth = min(20,lineWidth+1)
				if butt.pressed:
					butt.endPressed()
		elif event.type == pygame.MOUSEMOTION:
			# if event.buttons != (0,0,0): print("Drag with button")
			pass

	######################################################################
	# get the next set of coordinates
	######################################################################
	try:
		if channel == None:
			channel = serial.Serial(args.port)
			channel.timeout = 1
		line = channel.readline()[:-2]
	except KeyboardInterrupt:
		print("KeyboardInterrupt")
		running = False
		break
	except:
		if channel != None:
			channel.close()
			channel = None
		print("Exception on read, did the board disconnect ?")
		continue
	# the board sent "reset" to says it has reset
	if line == b"reset":
		print("SENT RESET")
	m = re.match(b'^\(([\d.-]+)(, *[\d.-]+)*\)$',line)
	if not m: continue
	# we have values !
	thisVal = [float(x) for x in re.findall(b'[\d.-]+',line)]
	
	if pauseGraph: continue
	if blankDraw: thisVal = []

	# set the next point (rolls over)
	position = progress % gwidth
	points[position] = thisVal
	backlog.append(thisVal)
	
	######################################################################
	# prepare the graphing data
	######################################################################
	# size up and init the min and max arrays
	while len(valMin) < len(thisVal): valMin += [None]
	while len(valMax) < len(thisVal): valMax += [None]
	while len(displayOn) < len(thisVal): displayOn += [True]
	for index in range(len(thisVal)):
		valMin[index] = thisVal[index]
		valMax[index] = thisVal[index]
	# compute the mins and maxs
	for pp in points:
		if pp != None:
			for index in range(len(pp)):
				valMin[index] = min(valMin[index],pp[index])
				valMax[index] = max(valMax[index],pp[index])
	# common axes (same min, same max for all axis)
	if axesCommon:
		# loop so we can skip the ones that are not on
		vvMin = max(valMin)
		for index in range(len(valMin)):
			if displayOn[index]:
				vvMin = min(valMin[index],vvMin)
		valMin = [vvMin] * len(valMin)
		vvMax = min(valMax)
		for index in range(len(valMax)):
			if displayOn[index]:
				vvMax = max(valMax[index],vvMax)
		valMax = [vvMax] * len(valMax)
	# centered axes (min = max so 0 is in the center for each axis)
	if axesCentered:
		for index in range(len(valMin)):
			vvMax = max(abs(valMin[index]),abs(valMax[index]))
			vvMax = vvMax + axesMargin*(valMax[index]-valMin[index])
			if valMin[index] > 0:
				valMin[index] = 0
			else:
				valMin[index] = -1*vvMax
			if valMax[index] < 0:
				valMax[index] = 0
			else:
				valMax[index] = vvMax
	# hide buttons by default
	for butt in listButtons:
		try:
			id = int(butt.id)
			if id <= len(displayOn):
				butt.visible = True
			else:
				butt.visible = False
		except:
			pass
	######################################################################
	# start drawing
	######################################################################
	# draw the background and axes
	pygame.draw.rect(screen,backgroundColor,pygame.Rect(gleft, gtop-1, gwidth+2, gheight+2))
	pygame.draw.rect(screen,axesColor,pygame.Rect(gleft, gtop-1, gwidth+2, gheight+2), width=1)
	for index in range(len(valMin)):
		if displayOn[index]:
			y = calcpos(0,valMin[index],valMax[index])
			pygame.draw.line(screen, colors[index], (gleft,y), (gwidth+gleft,y))
	# loop on all the points
	for tPos in range(len(points)):
		# skip non existing point
		if points[tPos] == None:
			previous = None
			continue
		# current points to draw
		current = points[tPos]
		# compute the position of the current point (because we roll over)
		drawPos = (gwidth-position+tPos-1) % (gwidth)
		# set the previous ([-1] is allowed)
		previous = points[tPos-1]
		if drawPos == 0 or previous == None:
			previous = current
		# draw the dots
		# print((max(0,drawPos-1),previous[0]), (drawPos,current[0]))
		for index in range(len(current)):
			if not displayOn[index]: continue
			color = colors[index]
			currValue = calcpos(current[index],valMin[index],valMax[index])
			if index < len(previous):
				prevValue = calcpos(previous[index],valMin[index],valMax[index])
			else:
				prevValue = currValue
			#pygame.draw.circle(screen,(50,255,255),(drawPos,prevValue),2)
			#pygame.draw.circle(screen,color,(drawPos,currValue),2)
			pygame.draw.line(screen, color, (max(0,drawPos-1),prevValue), (drawPos,currValue), width=lineWidth)
	# draw the rectangle around the graph backgroundColor
	pygame.draw.rect(screen, backgroundColor, pygame.Rect(0,0, screen_size[0], gtop-1), width=0)
	pygame.draw.rect(screen, backgroundColor, pygame.Rect(0, gtop+gheight+1, screen_size[0], screen_size[1]-(gtop+gheight)), width=0)
	# draw the buttons over everything else
	reDrawButtons()
	######################################################################
	# finished drawing
	######################################################################
	
	# loop stuff
	progress = (progress + 1) % (gwidth*3600)
