import pygame
import sys
import time


SCREEN_WIDTH = 1120
SCREEN_HEIGHT = 650
SQUARE_WIDTH = 65
BOARD_WIDTH = 600


def load_image(img_file_name):
	image = pygame.image.load("images/" + img_file_name)
	return image.convert_alpha()


def get_coordinate(position):
	""" Takes (row, col) and returns the coordinate of the index in the xy-plane """
	row, col = position
	return 300 + col*SQUARE_WIDTH, 65 + row*SQUARE_WIDTH

def highlight_border(surface, position, color):
	""" Takes a position and draws a border for the square at the position in the given color """
	x, y = get_coordinate(position)
	pygame.draw.rect(surface, color, (x+2, y+2, SQUARE_WIDTH-3, SQUARE_WIDTH-3), width=4)

def is_valid_position(position):
	""" Checks whether a given position is valid in a 8x8 board """
	return 0 <= position[0] < 8 and 0 <= position[1] < 8

def find_all_moves(board, steps, find_new_pos):
	""" Takes a function that returns a position by taking each step of steps and 
	returns the positions from nearest to farthest until it gets blocked by a piece """
	moves = []
	for step in steps:
		move_row, move_col = find_new_pos(step)
		if is_valid_position((move_row, move_col)):
			moves.append((move_row, move_col))
			if board[move_row][move_col]:
				break
	return moves

def is_hovered(position):
	""" Checks whether a position in the chess board is hovered by the mouse """
	x_coor, y_coor = get_coordinate(position)
	mouse_pos = pygame.mouse.get_pos()
	return x_coor <= mouse_pos[0] <= x_coor + SQUARE_WIDTH and \
		y_coor <= mouse_pos[1] <= y_coor + SQUARE_WIDTH

def render_text(text, font_size, color):
	""" Returns a rendered form of given text in given font_size and color """
	font = pygame.font.SysFont("courier", font_size, bold=True)
	return font.render(text, color, True)

def show_result(surface, game_result, center):
	""" Displays a formatted result of the game on screen """
	win = game_result in ["black", "white"]
	center_x, center_y = center

	if win:
		reason = "Checkmate"
	elif game_result == "stalemate":
		reason = "Stalemate"
	elif game_result == "50-move":
		reason = "Fifty-move Rule"
	else:
		reason = "No possible way to win"

	reason = render_text(reason, 32, (0, 0, 0))
	reason_width, reason_height = reason.get_width(), reason.get_height()
	surface.blit(reason, reason.get_rect(center=(center_x, center_y-80)))

	if win:
		result = render_text(f"{game_result.title()} wins!", 45, (0, 0, 0))
	else:
		result = render_text("Match draw!", 45, (0, 0, 0))

	result_width, result_height = result.get_width(), result.get_height()
	pygame.draw.rect(surface, (0, 0, 0), pygame.Surface((result_width+110, result_height+10)).get_rect(center=center))
	pygame.draw.rect(surface, (200, 200, 200), pygame.Surface((result_width+100, result_height)).get_rect(center=center))
	surface.blit(result, result.get_rect(center=center))

	retry_text = render_text("Press SPACE to play again!", 28, (0, 0, 0))
	surface.blit(retry_text, retry_text.get_rect(center=(center_x, center_y+80)))
	
	pygame.display.update()


class Piece:
	""" A template class for all pieces in the chess board """
	def __init__(self, position, color):
		self.position = position
		self.color = color

	def move_to(self, board, new_position):
		""" Moves this piece to the given new_position on the chess board """
		old_row, old_col = self.position
		new_row, new_col = new_position
		board[new_row][new_col] = self
		board[old_row][old_col] = None
		self.position = new_position

	def display(self, surface, img_file_name):
		image = load_image(img_file_name)
		surface.blit(image, get_coordinate(self.position))


class King(Piece):
	is_first_move = True

	def possible_moves(self, board):
		row, col = self.position
		moves = []
		# All squares around its position
		possibles = [(row+i, col+j) for i, j in [(0, -1), (0, 1), (-1, 0), (1, 0), 
			(-1, -1), (-1, 1), (1, -1), (1, 1)]]
		
		# Validates all possible moves
		for move in possibles:
			i, j = move
			if is_valid_position(move):
				if type(board[i][j]) == King:
					continue
				if board[i][j] and board[i][j].color == self.color:
					continue
				is_check = False
				other_piece = board[i][j]
				self.move_to(board, move)
				for x in board:
					for piece in x:
						if not piece or piece.color == self.color:
							continue
						if type(piece) == King:
							continue
						if move in piece.possible_moves(board):
							is_check = True
							break
					if is_check:
						break
				else:
					moves.append(move)
				self.move_to(board, (row, col))
				board[i][j] = other_piece
		
		# Castling move if it is his first move
		if self.is_first_move and not self.is_check(board):
			if not any(board[row][1:4]) and type(board[row][0]) == Rook and board[row][0].is_first_move:
				moves.append((row, col-2))
			if not any(board[row][5:7]) and type(board[row][7]) == Rook and board[row][7].is_first_move:
				moves.append((row, col+2))
		
		return moves

	def is_check(self, board):
		for row in board:
			for piece in row:
				if piece and piece.color != self.color:
					if type(piece) == King:
						continue
					if self.position in piece.possible_moves(board):
						return True
		return False

	def is_checkmate(self, board):
		checkmate = self.is_check(board) and len(self.possible_moves(board)) == 0
		
		if not checkmate:
			return False
		
		# Checks for any other piece's move that can avoid the checkmate
		for row in board:
			for piece in row:
				if piece and piece.color == self.color:
					for new_position in piece.possible_moves(board):
						if not is_valid_position(new_position):
							continue
						i, j = new_position
						if board[i][j] and board[i][j].color == piece.color:
							continue
						old_position = piece.position
						other_piece = board[i][j]
						piece.move_to(board, new_position)
						if not self.is_check(board):
							checkmate = False
						piece.move_to(board, old_position)
						board[i][j] = other_piece
						if not checkmate:
							return False
		
		return checkmate

	def display(self, surface):
		super().display(surface, f"{self.color}_king.png")


class Queen(Piece):
	def possible_moves(self, board):
		row, col = self.position
		moves = []

		# Vertically top
		moves += find_all_moves(board, range(1, row+1), lambda step: (row-step, col))
		# Vertically bottom
		moves += find_all_moves(board, range(1, 8-row), lambda step: (row+step, col))
		# Horizontally left
		moves += find_all_moves(board, range(1, col+1), lambda step: (row, col-step))
		# Horizontally right
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row, col+step))

		# Towards topleft
		moves += find_all_moves(board, range(1, col+1), lambda step: (row-step, col-step))
		# Towards bottomleft
		moves += find_all_moves(board, range(1, col+1), lambda step: (row+step, col-step))
		# Towards topright
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row-step, col+step))
		# Towards bottomright
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row+step, col+step))
		
		return moves

	def display(self, surface):
		super().display(surface, f"{self.color}_queen.png")


class Rook(Piece):
	is_first_move = True

	def possible_moves(self, board):
		row, col = self.position
		moves = []
		
		# Vertically top
		moves += find_all_moves(board, range(1, row+1), lambda step: (row-step, col))
		# Vertically bottom
		moves += find_all_moves(board, range(1, 8-row), lambda step: (row+step, col))
		# Horizontally left
		moves += find_all_moves(board, range(1, col+1), lambda step: (row, col-step))
		# Horizontally right
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row, col+step))
		
		return moves

	def display(self, surface):
		super().display(surface, f"{self.color}_rook.png")


class Knight(Piece):
	def possible_moves(self, board):
		row, col = self.position
		# All 'L' shape moves from his position
		moves = [(row+i, col+j) for i, j in [(-2, -1), (-2, 1), (-1, 2), (1, 2), 
			(-1, -2), (1, -2), (2, -1), (2, 1)]]
		return moves

	def display(self, surface):
		super().display(surface, f"{self.color}_knight.png")


class Bishop(Piece):
	def possible_moves(self, board):
		row, col = self.position
		moves = []

		# Towards topleft
		moves += find_all_moves(board, range(1, col+1), lambda step: (row-step, col-step))
		# Towards bottomleft
		moves += find_all_moves(board, range(1, col+1), lambda step: (row+step, col-step))
		# Towards topright
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row-step, col+step))
		# Towards bottomright
		moves += find_all_moves(board, range(1, 8-col), lambda step: (row+step, col+step))

		return moves

	def display(self, surface):
		super().display(surface, f"{self.color}_bishop.png")


class Pawn(Piece):
	is_first_move = True
	en_passant_side = ""

	def possible_moves(self, board):
		row, col = self.position
		moves = []
		
		direction = -1 if self.color == "white" else 1
		
		# Left capture moves (normal capture or en passant move)
		if is_valid_position((row+direction, col-1)):
			if board[row+direction][col-1] or self.en_passant_side == "left":
				moves.append((row+direction, col-1))
		# Right capture moves (normal capture or en passant move)
		if is_valid_position((row+direction, col+1)):
			if board[row+direction][col+1] or self.en_passant_side == "right":
				moves.append((row+direction, col+1))
		# Forward move in its direction
		if is_valid_position((row+direction, col)) and board[row+direction][col]:
			return moves
		moves.append((row+direction, col))
		
		# If it is his first move, then 2 steps move
		if self.is_first_move:
			if is_valid_position((row+2*direction, col)) and board[row+2*direction][col]:
				return moves
			moves.append((row+2*direction, col))
		
		return moves

	def display(self, surface):
		super().display(surface, f"{self.color}_pawn.png")


class Chess:
	def __init__(self):
		self.board = [
			[Rook((0, 0), "black"), Knight((0, 1), "black"), Bishop((0, 2), "black"), Queen((0, 3), "black"), 
				King((0, 4), "black"), Bishop((0, 5), "black"), Knight((0, 6), "black"), Rook((0, 7), "black")], 
			[Pawn((1, i), "black") for i in range(8)], 
			[None for i in range(8)], 
			[None for i in range(8)], 
			[None for i in range(8)], 
			[None for i in range(8)], 
			[Pawn((6, i), "white") for i in range(8)], 
			[Rook((7, 0), "white"), Knight((7, 1), "white"), Bishop((7, 2), "white"), Queen((7, 3), "white"), 
				King((7, 4), "white"), Bishop((7, 5), "white"), Knight((7, 6), "white"), Rook((7, 7), "white")]
		]
		self.board_image = load_image("chess_board.jpg")
		self.black_king = self.board[0][4]
		self.white_king = self.board[7][4]
		self.selected_piece = None
		self.player_turn = "white"
		self.num_moves_last_capture = 0

	def pawn_promotion(self, surface):
		""" When the pawn reaches the other end of the chess board, 
		the player can take Queen / Bishop / Knight / Rook """
		pawn = self.selected_piece
		x_coor, y_coor = get_coordinate(pawn.position)
		row, col = pawn.position
		color = pawn.color
		start_row = row if color == "white" else row-3
		choice_pieces = [piece((start_row+i, col), color) for i, piece in enumerate([Queen, Bishop, Knight, Rook])]
		
		# Displays all option pieces from which a new piece can be selected
		for i, piece in enumerate(choice_pieces):
			box_x, box_y = get_coordinate(piece.position)
			pygame.draw.rect(surface, (0, 0, 0), (box_x-1, box_y-1, SQUARE_WIDTH+2, SQUARE_WIDTH+2), width=4)
			pygame.draw.rect(surface, (200, 200, 200), (box_x, box_y, SQUARE_WIDTH, SQUARE_WIDTH))
			piece.display(surface)
		pygame.display.update()
		
		# Waits for the user to select a piece and returns the piece
		new_piece = None
		while not new_piece:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.MOUSEBUTTONDOWN:
					mouse_pos = pygame.mouse.get_pos()
					for piece in choice_pieces:
						if is_hovered(piece.position):
							new_piece = piece
							break

		new_piece.position = pawn.position
		return new_piece

	def remove_moves_causing_check(self, moves, piece):
		""" Removes all moves that causes check to its own king """
		wrong_moves = []
		for new_position in moves:
			if not is_valid_position(new_position):
				continue

			old_position = piece.position
			new_row, new_col = new_position
			
			other_piece = self.board[new_row][new_col]
			piece.move_to(self.board, new_position)
			
			king = self.white_king if piece.color == "white" else self.black_king
			if king.is_check(self.board):
				wrong_moves.append(new_position)
			
			piece.move_to(self.board, old_position)
			self.board[new_row][new_col] = other_piece

		for move in wrong_moves:
			moves.remove(move)

		return moves

	def is_draw(self):
		# Checks whether any player cannot make a move but also not in check
		# or whether there are no pieces other than the two kings who cannot capture each other
		can_white_move = False
		can_black_move = False
		
		num_pieces_alive = 0
		num_kings_alive = 0
		
		for row in self.board:
			for piece in row:
				if not piece:
					continue
				
				num_pieces_alive += 1
				if type(piece) == King:
					num_kings_alive += 1
				
				possible_moves = piece.possible_moves(self.board)
				possible_moves = list(filter(is_valid_position, possible_moves))
				self.remove_moves_causing_check(possible_moves, piece)
				if possible_moves:
					if piece.color == "white":
						can_white_move = True
					else:
						can_black_move = True

		if num_pieces_alive == num_kings_alive == 2:
			return True
		return not can_white_move or not can_black_move

	def display_board(self, surface):
		# Background color
		surface.fill((255, 255, 255))

		# Chess board
		surface.blit(self.board_image, ((SCREEN_WIDTH-BOARD_WIDTH)/2, (SCREEN_HEIGHT-BOARD_WIDTH)/2))
		# Pieces
		for row in self.board:
			for piece in row:
				if piece is None:
					continue
				piece.display(surface)

		# Highlights the selected_piece and its possible moves
		if self.selected_piece:
			piece = self.selected_piece
			row, col = piece.position
			highlight_border(surface, (row, col), (0, 0, 200))
			possible_moves = piece.possible_moves(self.board)
			self.remove_moves_causing_check(possible_moves, piece)
			for move in possible_moves:
				i, j = move
				if is_valid_position((i, j)):
					if self.board[i][j]:
						if self.board[i][j].color != piece.color:
							highlight_border(surface, move, (200, 0, 0))
					else:
						highlight_border(surface, move, (0, 200, 0))

					# En passant capture
					if type(piece) == Pawn and piece.en_passant_side:
						if (piece.en_passant_side == "left" and j == col-1) or \
								(piece.en_passant_side == "right" and j == col+1):
							highlight_border(surface, move, (200, 0, 0))
					
		# If not selected, highlights the king if he is in check
		elif self.black_king.is_check(self.board):
			highlight_border(surface, self.black_king, (200, 0, 0))
		elif self.white_king.is_check(self.board):
			highlight_border(surface, self.white_king, (200, 0, 0))

		pygame.display.update()

	def play(self, surface):
		""" Main chess game """
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.MOUSEBUTTONDOWN:
					for i in range(8):
						for j in range(8):
							if not is_hovered((i, j)):
								continue
							# If a position is clicked and a piece is already selected
							if self.selected_piece:
								piece = self.selected_piece

								if not self.board[i][j] or self.board[i][j].color != piece.color:
									# Possible moves of the selected piece
									possible_moves = piece.possible_moves(self.board)
									self.remove_moves_causing_check(possible_moves, piece)
									
									if (i, j) in possible_moves:
										self.num_moves_last_capture += 1

										# 50-move rule
										if type(piece) == Pawn or self.board[i][j]:
											self.num_moves_last_capture = 0
										if self.num_moves_last_capture >= 100:
											self.game_over(surface, "50-move")

										# Game over if king is captured
										if type(self.board[i][j]) == King:
											self.game_over(surface, piece.color)
										
										if type(piece) == Pawn:
											# En passant
											side = piece.en_passant_side
											pawn_row, pawn_col = piece.position
											
											if side:
												direction = -1 if piece.color == "white" else 1
												# Left capture move or Right capture move
												if (side == "left" and j == pawn_col-1) or (side == "right" and j == pawn_col+1):
													self.board[i-direction][j] = None

											if piece.is_first_move and abs(pawn_row-i) == 2:
												for col, en_passant_side in ((j-1, "right"), (j+1, "left")):
													if is_valid_position((i, col)):
														side_piece = self.board[i][col]
														if type(side_piece) == Pawn and side_piece.color != piece.color:
															side_piece.en_passant_side = en_passant_side

											# Pawn Promotion when he reaches the other end of the chess board
											if i in (0, 7):
												piece = self.pawn_promotion(surface)

										# Checks whether the move is castle
										if type(piece) == King:
											if piece.is_first_move:
												row, col = piece.position
												# King side castle
												if col+2 == j:
													if type(self.board[row][col+3]) == Rook:
														rook = self.board[row][col+3]
														if rook.is_first_move:
															rook.move_to(self.board, (row, col+1))
												# Queen side castle
												if col-2 == j:
													if type(self.board[row][col-4]) == Rook:
														rook = self.board[row][col-4]
														if rook.is_first_move:
															rook.move_to(self.board, (row, col-1))
											
										if type(piece) in [Pawn, King, Rook]:
											piece.is_first_move = False

										piece.move_to(self.board, (i, j))

										for row in range(2, 6):
											for col in self.board[row]:
												if col and type(col) == Pawn and col.color == piece.color:
													col.en_passant_side = ""

										# White causes check to black, white wins
										if piece.color == "white":
											if self.black_king.is_checkmate(self.board):
												self.game_over(surface, "white")
										# Black causes check to white, black wins
										elif self.white_king.is_checkmate(self.board):
											self.game_over(surface, "black")
										
										# Match draw
										if self.is_draw():
											# Checks whether it is stalemate
											if not self.black_king.possible_moves(self.board) or not self.white_king.possible_moves(self.board):
												self.game_over(surface, "stalemate")
											else:
												self.game_over(surface, "normal-draw")

										self.selected_piece = None
										self.player_turn = "white" if self.player_turn == "black" else "black"
								else:
									# Selects a new piece in the same color
									self.selected_piece = self.board[i][j]
							
							# If a piece is clicked and no piece is selected
							else:
								if not self.board[i][j]:
									continue
								# Selects the piece if it is the piece's color turn
								if self.board[i][j].color == self.player_turn:
									self.selected_piece = self.board[i][j]

			# Displays chess board, pieces, and possible moves of selected piece
			self.display_board(surface)

	def game_over(self, surface, game_result):
		checkmate_king = None
		stalemate_king = None

		if game_result == "white":
			checkmate_king = self.black_king
		elif game_result == "black":
			checkmate_king = self.white_king

		if game_result == "stalemate":
			if not self.black_king.possible_moves(self.board):
				stalemate_king = self.black_king
			else:
				stalemate_king = self.white_king
		
		surface.fill((255, 255, 255))
		
		# Displays chess board in the left side
		surface.blit(self.board_image, ((SCREEN_WIDTH-BOARD_WIDTH)/2-(3.5*SQUARE_WIDTH), (SCREEN_HEIGHT-BOARD_WIDTH)/2))

		for row in self.board:
			for piece in row:
				if piece:
					# Displays all pieces on the board
					piece.position = (piece.position[0], piece.position[1]-3.5)
					piece.display(surface)
					
					# Highlights the checkmate_king psoition
					if checkmate_king and piece == checkmate_king:
						highlight_border(surface, piece.position, (200, 0, 0))

		# Highlights the stalemate_king position if it was a stalemate
		if stalemate_king:
			highlight_border(surface, stalemate_king.position, (0, 0, 200))

		# Displays the game_result and retry text
		center_x = SCREEN_WIDTH-240
		center_y = SCREEN_HEIGHT/2
		
		show_result(surface, game_result, (center_x, center_y))
		
		# Retry if SPACE pressed or Quit if game window closed
		retry = False
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_SPACE:
						self.__init__()
						retry = True
						break
			if retry:
				break
		self.play(surface)


def main():
	pygame.init()

	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

	chess_icon = load_image("chess_icon.png")
	pygame.display.set_caption("Chess Tournament")
	pygame.display.set_icon(chess_icon)

	my_chess = Chess()
	my_chess.play(screen)


if __name__ == "__main__":
	main()


