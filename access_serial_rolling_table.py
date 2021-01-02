import serial, re, math
from serial.tools.list_ports import comports

test_port = "/dev/tty.usbmodem7CDFA103B7B41"

colors = [
	(255,0,0),
	(255,255,0),
	(0,255,0),
	(0,255,255),
	(0,0,255),
	(255,0,255),
]

screen_size = [800,600]
gleft = 0
gtop = 0
gwidth = 800
gheight = 600

# import basic pygame modules
import pygame # as pg
screen_flags = pygame.HWSURFACE | pygame.DOUBLEBUF
#screen_flags |= pygame.FULLSCREEN

pygame.init()
pygame.display.init()
window = pygame.display.set_mode(screen_size,screen_flags)
screen = pygame.display.get_surface()

# serial
channel = serial.Serial(test_port)

# loop stuff
progress = 0
previous = None
backs = [(0,0,0),(255,255,255)]
points = [(0,0,0)] * gwidth
npoints = 0

running = True
while running:
	line = channel.readline()[:-2]
	m = re.match(b'^\(([\d.]+)(, *[\d.]+)*\)$',line)
	if line == "reset":
		print("RESET")
		channel.close()
		pygame.draw.line(screen,(0,0,50), (position,gtop),(position,gtop+gheight),2)
		time.sleep(2)
		channel = serial.Serial(test_port)
	
	if not m: continue

	# rolling graph
	position = progress % gwidth
	back = backs[(progress//gwidth) % len(backs)]
	
	l = [float(x) for x in re.findall(b'[\d.]+',line)]
	cl = [val * gheight/255 + gtop for val in l]
	points[position] = cl
	print(position,cl)

	for drawPos in range(position):
		current = points[drawPos]
		if drawPos == 0: previous = current
		# clean screen
		pygame.draw.line(screen,back,(drawPos+1,gtop),(drawPos+1,gtop+gheight),2)
		print(drawPos,current,previous)
		# draw the dots
		for index in range(len(current)):
			color = colors[index]
			#pygame.draw.circle(screen,color,(drawPos,current[index]),1)
			#pygame.draw.circle(screen,color,(drawPos-1,previous[index]),1)
			pygame.draw.line(screen, color, (drawPos-1,previous[index]), (drawPos,current[index]))
		previous = current
	
	# loop stuff
	progress = (progress + 1) % (gwidth*3600)
	
	# event loop and display stuff
	pygame.display.flip()
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

