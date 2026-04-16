import numpy as np
import random, pygame

pygame.font.init()

rows = 20
columns = 10
block = 30 #block size
width = 300
height = 600
bg_color = (0,0,0)
score = 0

board = np.zeros((rows,columns))

L = np.array([[0,0,1], [1,1,1]])
J = np.array([[1,0,0], [1,1,1]])
T = np.array([[1,1,1], [0,1,0]])
S = np.array([[0,1,1], [1,1,0]])
Z = np.array([[1,1,0], [0,1,1]])
Bar = np.array([[1,1,1,1]])
Box = np.array([[1,1], [1,1]])


shapes = [L, T, J, S, Z, Bar, Box]

class Tetraminoe:

	def __init__(self):
		self.shape = np.rot90(random.choice(shapes), random.randint(0,3))
		self.color = (random.randint(30, 255), random.randint(30, 255), random.randint(30, 255))
		self.row = 0
		self.column = int(columns/3)

def get_random_tetraminoe():

	return Tetraminoe()

def draw_grid(background):

	for i, row in enumerate(board):
		#Draw horizontal lines
		pygame.draw.line(background, (50,50,50), (0,0+(i*block)), (width, 0+(i*block)), 1)
		for j, column in enumerate(row):
			#Draw vertical lines
			pygame.draw.line(background, (50,50,50), (0+(i*block),0), (0+(i*block),height), 1)

def get_coordinates(tetraminoe):

	coordinates = []

	for i, row in enumerate(tetraminoe.shape):
		for j, column in enumerate(row):
			if column == 1:
				coordinates.append((i+tetraminoe.row,j+tetraminoe.column))

	return coordinates

def lock_coordinates(coordinates, tetraminoe, locked):
	
	for x,y in coordinates:
		board[x,y] = 1 
		locked.update({(x,y):tetraminoe.color})

def draw_on_board(background, tetraminoe, locked):

	coordinates = get_coordinates(tetraminoe)
	
	for (x,y) in coordinates:
		board[x,y] = 1
	
	for i, row in enumerate(board):
		for j, column in enumerate(row):
			if (i,j) in locked:
				board[i,j] = 1
				pygame.draw.rect(background, locked[(i,j)], pygame.Rect(0+(j*block), 0+(i*block), block, block))
			elif board[i,j] == 1:
				pygame.draw.rect(background, tetraminoe.color, pygame.Rect(0+(j*block), 0+(i*block), block, block))

def falling(tetraminoe):

	coordinates = get_coordinates(tetraminoe)

	for (x,y) in coordinates:
		#If about to hit the bottom
		if x == rows-1:
			return False
		#If about to touch another tetraminoe
		elif board[x+1, y] == 1 and (x+1, y) not in coordinates:
			return False

	return True

def move_tetraminoe(tetraminoe):

	left_valid, right_valid, down_valid = True, True, True

	coordinates = get_coordinates(tetraminoe)

	for (x,y) in coordinates:
		#Move to the left
		if y == 0:
			left_valid = False
		elif board[x, y-1] == 1 and (x, y-1) not in coordinates:
			left_valid = False
		#Move to the right
		if y == columns-1:
			right_valid = False
		elif board[x, y+1] == 1 and (x, y+1) not in coordinates:
			right_valid = False
		#Move down
		if x == rows-1:
			down_valid = False
		elif board[x+1, y] == 1 and (x+1, y) not in coordinates:
			down_valid = False

	return left_valid, right_valid, down_valid

def rotation_valid(tetraminoe):

	current_coordinates = get_coordinates(tetraminoe)

	taken_coordinates = []

	for i, row in enumerate(board):
		for j ,column in enumerate(row):
			if board[i,j] == 1:
				taken_coordinates.append((i,j))

	rotated_tetraminoe = np.rot90(tetraminoe.shape, 1)

	rotated_coordinates = []

	for i, row in enumerate(rotated_tetraminoe):
		for j, column in enumerate(row):
			if column == 1:
				rotated_coordinates.append((i+tetraminoe.row,j+tetraminoe.column))

	for (x,y) in rotated_coordinates:
		#If roated tetraminoe uses taken coordinates
		if (x,y) in taken_coordinates and (x,y) not in current_coordinates:
			return False
		#If rotated tetraminoe goes beyond the index
		elif (y > columns-1) or (x > rows-1):
			return False

	return True

def erase_footprints(tetraminoe):

	coordinates = get_coordinates(tetraminoe)

	for (x,y) in coordinates:
		board[x, y] = 0 

def clear_lines(locked):
	global score
	cleared_lines = 0

	for i, row in enumerate(board):
		#If full line delete all columns
		if np.sum(row) == columns:
			for j, column in enumerate(row):
				locked.pop((i,j), None)
				board[i, j] = 0

			cleared_lines += 1
			cleared_line_idx = i
			score += 1 
			
	if cleared_lines > 0:
		for (x,y) in sorted(list(locked), reverse=True):
			if x < cleared_line_idx:
				locked[(x+cleared_lines,y)] = locked.pop((x,y), None)
				board[x,y] = 0
	
def is_gameover(locked):

	for (x,y) in sorted(locked):
		if x == 0:
			return True

	return False

def print_score(screen):
	#Turn screen black
	screen.fill((0,0,0))
	font = pygame.font.SysFont('Comic Sans MS', 40)
	textsurface = font.render('Lines cleared: {}'.format(score), False, (255,255,255))
	screen.blit(textsurface,(width/6,height/2))

def main():
	global board

	screen = pygame.display.set_mode((width, height))
	pygame.display.set_caption('Tetris')

	is_using_program = True

	#Dictionary of locked coordinates, (x,y): color
	locked = {}
	change_piece = None
	tetraminoe = get_random_tetraminoe()

	clock = pygame.time.Clock()
	fall_speed = 0.3
	fall_time = 0

	#Game loop
	while(is_using_program):

		draw_on_board(screen, tetraminoe, locked)

		fall_time += clock.get_rawtime()
		clock.tick()
 
		if fall_time/1000 >= fall_speed:
			fall_time = 0

			if falling(tetraminoe):
				erase_footprints(tetraminoe)
				tetraminoe.row += 1
			else:
				#If piece hits the bottom, lock current coordinates and get new piece
				current_coor = get_coordinates(tetraminoe)
				lock_coordinates(current_coor, tetraminoe, locked)

				tetraminoe = get_random_tetraminoe()

				clear_lines(locked)

		for event in pygame.event.get():

			if event.type == pygame.QUIT:
				is_using_program = False

			left_valid, right_valid, down_valid = move_tetraminoe(tetraminoe)

			if event.type == pygame.KEYDOWN:

				if event.key == pygame.K_RIGHT:
					if right_valid:
						erase_footprints(tetraminoe)
						tetraminoe.column += 1

				if event.key == pygame.K_LEFT:
					if left_valid:
						erase_footprints(tetraminoe)
						tetraminoe.column -= 1

				if event.key == pygame.K_UP:
					if rotation_valid(tetraminoe):
						erase_footprints(tetraminoe)
						tetraminoe.shape = np.rot90(tetraminoe.shape, 1)

				if event.key == pygame.K_DOWN:
					if down_valid:
						erase_footprints(tetraminoe)
						tetraminoe.row += 1

		draw_grid(screen)
		#print(board)

		if is_gameover(locked):
			print_score(screen)

		#Refresh window
		pygame.display.flip()
		screen.fill(bg_color)

main()
