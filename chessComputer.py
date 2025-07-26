import pygame
import sys
import random
from typing import List, Tuple, Optional, Dict, Any

# Initialize pygame
pygame.init()

# Constants
BOARD_SIZE = 640
CONTROL_PANEL_HEIGHT = 100
WIDTH, HEIGHT = BOARD_SIZE, BOARD_SIZE + CONTROL_PANEL_HEIGHT
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS
PIECE_SCALE = 0.8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (247, 247, 105, 150)
MOVE_HIGHLIGHT = (100, 255, 100, 150)
CHECK_HIGHLIGHT = (255, 50, 50, 200)
TIMER_BG = (255, 255, 255)
WHITE_TIMER_COLOR = (240, 240, 240)
BLACK_TIMER_COLOR = (30, 30, 30)
MESSAGE_COLOR = (220, 220, 220)
BUTTON_COLOR = (80, 80, 100)
BUTTON_HOVER = (120, 120, 140)
PROMOTE_BG = (50, 50, 70, 200)
SETTINGS_BG = (40, 40, 60, 220)
CONTROL_BG = (70, 70, 90)

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

class Piece:
    def __init__(self, color: str, type: str):
        self.color = color
        self.type = type
        self.has_moved = False
        self.angle = 0

    def __repr__(self):
        return f"{self.color[0]}{self.type[0].upper()}"

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', font_size)
        self.is_hovered = False
        self.active = True
        
    def draw(self, surface: pygame.Surface):
        if not self.active:
            color = (50, 50, 50)
        else:
            color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        
        text_color = (150, 150, 150) if not self.active else WHITE
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos: Tuple[int, int]):
        self.is_hovered = self.active and self.rect.collidepoint(pos)
        
    def is_clicked(self, pos: Tuple[int, int], event: pygame.event.Event) -> bool:
        return (self.active and event.type == pygame.MOUSEBUTTONDOWN 
                and event.button == 1 and self.rect.collidepoint(pos))

class PromotionButton(Button):
    def __init__(self, x: int, y: int, size: int, piece_type: str, color: str):
        super().__init__(x, y, size, size, "")
        self.piece_type = piece_type
        self.color = color
        self.symbol_font = pygame.font.SysFont('Segoe UI Symbol', int(size * 0.7))
        
    def draw(self, surface: pygame.Surface):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        
        symbol = self.get_symbol()
        text_surf = self.symbol_font.render(symbol, True, WHITE if self.color == "white" else BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def get_symbol(self) -> str:
        symbols = {
            "queen": "♕",
            "rook": "♖",
            "bishop": "♗",
            "knight": "♘"
        }
        return symbols.get(self.piece_type, "?")

class Board:
    def __init__(self, vs_computer: bool = False, computer_color: str = "black"):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.setup_board()
        self.turn = "white"
        self.selected_piece = None
        self.valid_moves = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.check = False
        self.checkmate = False
        self.stalemate = False
        self.piece_symbols = self.create_piece_symbols()
        
        # Game timers
        self.initial_time = 10 * 60 * 1000  # 10 minutes in milliseconds
        self.white_time = self.initial_time
        self.black_time = self.initial_time
        self.last_time = pygame.time.get_ticks()
        self.game_over = False
        self.winner = None
        self.paused = False
        
        # Game modes
        self.vs_computer = vs_computer
        self.computer_color = computer_color
        self.computer_thinking = False
        
        # Promotion variables
        self.promoting = False
        self.promotion_pos = None
        self.promotion_buttons = []
        
        # UI buttons
        self.create_buttons()
        self.selecting_mode = True
        self.show_settings = False

    def create_buttons(self):
        # Mode selection buttons (main menu)
        button_width, button_height = 200, 40
        self.human_button = Button(
            WIDTH//2 - button_width//2, HEIGHT//2 - 60, 
            button_width, button_height, "Play vs Human"
        )
        self.computer_button = Button(
            WIDTH//2 - button_width//2, HEIGHT//2 + 10, 
            button_width, button_height, "Play vs Computer"
        )
        
        # Control buttons (below board)
        btn_width, btn_height = 100, 35
        margin = 15
        start_y = BOARD_SIZE + (CONTROL_PANEL_HEIGHT - btn_height) // 2
        
        self.pause_button = Button(
            margin, start_y, btn_width, btn_height, "Pause" if not self.paused else "Resume", 18
        )
        self.restart_button = Button(
            margin * 2 + btn_width, start_y, btn_width, btn_height, "Restart", 18
        )
        self.settings_button = Button(
            margin * 3 + btn_width * 2, start_y, btn_width, btn_height, "Settings", 18
        )
        
        # Settings menu buttons
        settings_btn_width = 180
        self.time_10m_button = Button(
            WIDTH//2 - settings_btn_width//2, HEIGHT//2 - 70, settings_btn_width, 40, "10 Minutes"
        )
        self.time_5m_button = Button(
            WIDTH//2 - settings_btn_width//2, HEIGHT//2 - 20, settings_btn_width, 40, "5 Minutes"
        )
        self.time_3m_button = Button(
            WIDTH//2 - settings_btn_width//2, HEIGHT//2 + 30, settings_btn_width, 40, "3 Minutes"
        )
        self.close_settings_button = Button(
            WIDTH//2 - settings_btn_width//2, HEIGHT//2 + 80, settings_btn_width, 40, "Close"
        )

    def create_piece_symbols(self) -> Dict[str, pygame.Surface]:
        symbols = {
            "king": "♔",
            "queen": "♕",
            "rook": "♖",
            "bishop": "♗",
            "knight": "♘",
            "pawn": "♙"
        }
        
        piece_surfaces = {}
        for piece_type, symbol in symbols.items():
            font = pygame.font.SysFont('Segoe UI Symbol', int(SQUARE_SIZE * PIECE_SCALE))
            text = font.render(symbol, True, WHITE)
            piece_surfaces[f"white_{piece_type}"] = text
            
            font = pygame.font.SysFont('Segoe UI Symbol', int(SQUARE_SIZE * PIECE_SCALE), bold=True)
            text = font.render(symbol, True, BLACK)
            piece_surfaces[f"black_{piece_type}"] = text
                
        return piece_surfaces

    def setup_board(self):
        # Set up pawns
        for col in range(8):
            self.board[1][col] = Piece("black", "pawn")
            self.board[6][col] = Piece("white", "pawn")

        # Set up rooks
        self.board[0][0] = self.board[0][7] = Piece("black", "rook")
        self.board[7][0] = self.board[7][7] = Piece("white", "rook")

        # Set up knights
        self.board[0][1] = self.board[0][6] = Piece("black", "knight")
        self.board[7][1] = self.board[7][6] = Piece("white", "knight")
        self.board[0][1].angle = 180
        self.board[0][6].angle = 180
        self.board[7][1].angle = 0
        self.board[7][6].angle = 0

        # Set up bishops
        self.board[0][2] = self.board[0][5] = Piece("black", "bishop")
        self.board[7][2] = self.board[7][5] = Piece("white", "bishop")

        # Set up queens
        self.board[0][3] = Piece("black", "queen")
        self.board[7][3] = Piece("white", "queen")

        # Set up kings
        self.board[0][4] = Piece("black", "king")
        self.board[7][4] = Piece("white", "king")

    def draw(self, screen: pygame.Surface):
        if self.selecting_mode:
            self.draw_mode_selection(screen)
            return
            
        # Draw chess board squares
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight selected piece and valid moves
        if self.selected_piece:
            row, col = self.selected_piece
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

            for move in self.valid_moves:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(MOVE_HIGHLIGHT)
                screen.blit(s, (move[1] * SQUARE_SIZE, move[0] * SQUARE_SIZE))

        # Highlight king in check
        if self.check and not self.checkmate:
            king_pos = self.white_king_pos if self.turn == "white" else self.black_king_pos
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(CHECK_HIGHLIGHT)
            screen.blit(s, (king_pos[1] * SQUARE_SIZE, king_pos[0] * SQUARE_SIZE))

        # Draw pieces
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    text_surface = self.piece_symbols[f"{piece.color}_{piece.type}"]
                    text_rect = text_surface.get_rect(
                        center=(col * SQUARE_SIZE + SQUARE_SIZE // 2,
                               row * SQUARE_SIZE + SQUARE_SIZE // 2)
                    )
                    if piece.type == "knight":
                        rotated = pygame.transform.rotate(text_surface, piece.angle)
                        rot_rect = rotated.get_rect(center=text_rect.center)
                        screen.blit(rotated, rot_rect)
                    else:
                        screen.blit(text_surface, text_rect)

        # Draw control panel background
        pygame.draw.rect(screen, CONTROL_BG, (0, BOARD_SIZE, WIDTH, CONTROL_PANEL_HEIGHT))
        
        # Draw promotion menu if active
        if self.promoting:
            self.draw_promotion_menu(screen)

        # Draw control buttons
        self.draw_control_buttons(screen)

        # Draw settings menu if active
        if self.show_settings:
            self.draw_settings_menu(screen)

        self.draw_timers(screen)
        self.draw_status_messages(screen)
        
        if self.vs_computer and self.computer_thinking and self.turn == self.computer_color:
            font = pygame.font.SysFont('Arial', 20)
            text = font.render("Computer is thinking...", True, BLACK)
            screen.blit(text, (10, 10))

    def draw_control_buttons(self, screen: pygame.Surface):
        # Update pause button text
        self.pause_button.text = "Resume" if self.paused else "Pause"
        
        # Draw control buttons
        self.pause_button.draw(screen)
        self.restart_button.draw(screen)
        self.settings_button.draw(screen)

    def draw_settings_menu(self, screen: pygame.Surface):
        # Draw semi-transparent background
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill(SETTINGS_BG)
        screen.blit(s, (0, 0))
        
        # Draw settings title
        font = pygame.font.SysFont('Arial', 30)
        text = font.render("Game Settings", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 120))
        
        # Draw time control buttons
        self.time_10m_button.draw(screen)
        self.time_5m_button.draw(screen)
        self.time_3m_button.draw(screen)
        self.close_settings_button.draw(screen)

    def draw_promotion_menu(self, screen: pygame.Surface):
        if not self.promotion_pos:
            return
            
        row, col = self.promotion_pos
        piece = self.board[row][col]
        if not piece or piece.type != "pawn":
            return
            
        color = piece.color
        
        # Draw semi-transparent background
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill(PROMOTE_BG)
        screen.blit(s, (0, 0))
        
        # Draw promotion options
        button_size = SQUARE_SIZE * 1.5
        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        
        # Create buttons if they don't exist
        if not self.promotion_buttons:
            types = ["queen", "rook", "bishop", "knight"]
            for i, piece_type in enumerate(types):
                x = center_x - (2 * button_size) + (i * button_size)
                y = center_y - button_size // 2
                self.promotion_buttons.append(
                    PromotionButton(x, y, button_size, piece_type, color))
        
        # Draw buttons
        font = pygame.font.SysFont('Arial', 30)
        text = font.render("Promote pawn to:", True, WHITE)
        screen.blit(text, (center_x - text.get_width()//2, center_y - button_size - 30))
        
        for button in self.promotion_buttons:
            button.draw(screen)

    def draw_mode_selection(self, screen: pygame.Surface):
        screen.fill(LIGHT_SQUARE)
        
        font = pygame.font.SysFont('Arial', 36)
        title = font.render("Chess Game", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
        
        font = pygame.font.SysFont('Arial', 24)
        subtitle = font.render("Select Game Mode", True, BLACK)
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2 - 100))
        
        self.human_button.draw(screen)
        self.computer_button.draw(screen)

    def draw_timers(self, screen: pygame.Surface):
        # Draw timer background
        timer_height = 30
        pygame.draw.rect(screen, TIMER_BG, (0, BOARD_SIZE, WIDTH, timer_height))
        
        def format_time(ms):
            seconds = max(0, ms // 1000)
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        
        # Draw white timer (top right)
        white_text = format_time(self.white_time)
        font = pygame.font.SysFont('Arial', 24)
        text_surface = font.render(white_text, True, WHITE_TIMER_COLOR)
        screen.blit(text_surface, (WIDTH - 100, BOARD_SIZE + 5))
        
        # Draw black timer (top left)
        black_text = format_time(self.black_time)
        text_surface = font.render(black_text, True, BLACK_TIMER_COLOR)
        screen.blit(text_surface, (20, BOARD_SIZE + 5))

    def draw_status_messages(self, screen: pygame.Surface):
        font = pygame.font.SysFont('Arial', 20)
        status_y = BOARD_SIZE + 40
        
        if self.checkmate:
            winner = "Black" if self.turn == "white" else "White"
            text = font.render(f"Checkmate! {winner} wins!", True, MESSAGE_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, status_y))
            
        elif self.stalemate:
            text = font.render("Stalemate! Game drawn.", True, MESSAGE_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, status_y))
            
        elif self.check:
            text = font.render("Check!", True, MESSAGE_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, status_y))
        elif self.game_over and self.winner:
            text = font.render(f"Time's up! {self.winner} wins!", True, MESSAGE_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, status_y))
        else:
            turn_text = f"{self.turn.capitalize()}'s turn"
            if self.vs_computer and self.turn == self.computer_color:
                turn_text = "Computer's turn"
            text = font.render(turn_text, True, MESSAGE_COLOR)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, status_y))

    def update_timers(self):
        if self.game_over or self.selecting_mode or self.promoting or self.paused or self.show_settings:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.last_time
        self.last_time = current_time
        
        if self.turn == "white":
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.game_over = True
                self.winner = "Black"
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.game_over = True
                self.winner = "White"

    def toggle_pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.last_time = pygame.time.get_ticks()  # Reset timer when unpausing

    def restart_game(self):
        self.__init__(vs_computer=self.vs_computer, computer_color=self.computer_color)
        self.white_time = self.initial_time
        self.black_time = self.initial_time

    def set_time_control(self, minutes: int):
        self.initial_time = minutes * 60 * 1000
        self.white_time = self.initial_time
        self.black_time = self.initial_time
        self.show_settings = False

    def is_in_check(self, color: str, board: Optional[List[List[Optional[Piece]]]] = None) -> bool:
        if board is None:
            board = self.board
            
        king_pos = self.white_king_pos if color == "white" else self.black_king_pos
        opponent_color = "black" if color == "white" else "white"
        
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent_color:
                    if self.is_valid_move_for_piece((row, col), king_pos, board):
                        return True
        return False

    def is_valid_move_for_piece(self, start: Tuple[int, int], end: Tuple[int, int], 
                              board: List[List[Optional[Piece]]]) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        piece = board[start_row][start_col]

        if not piece:
            return False

        target_piece = board[end_row][end_col]
        if target_piece and target_piece.color == piece.color:
            return False

        if piece.type == "pawn":
            direction = -1 if piece.color == "white" else 1
            if start_col == end_col and not target_piece:
                if (end_row == start_row + direction) or (
                    not piece.has_moved and end_row == start_row + 2 * direction and not board[start_row + direction][start_col]
                ):
                    return True
            elif abs(end_col - start_col) == 1 and end_row == start_row + direction:
                if target_piece and target_piece.color != piece.color:
                    return True

        elif piece.type == "knight":
            return (abs(end_row - start_row) == 2 and abs(end_col - start_col) == 1) or (
                abs(end_row - start_row) == 1 and abs(end_col - start_col) == 2
            )

        elif piece.type == "bishop":
            if abs(end_row - start_row) == abs(end_col - start_col):
                row_step = 1 if end_row > start_row else -1
                col_step = 1 if end_col > start_col else -1
                r, c = start_row + row_step, start_col + col_step
                while r != end_row and c != end_col:
                    if board[r][c]:
                        return False
                    r += row_step
                    c += col_step
                return True

        elif piece.type == "rook":
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for c in range(start_col + step, end_col, step):
                    if board[start_row][c]:
                        return False
                return True
            elif start_col == end_col:
                step = 1 if end_row > start_row else -1
                for r in range(start_row + step, end_row, step):
                    if board[r][start_col]:
                        return False
                return True

        elif piece.type == "queen":
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for c in range(start_col + step, end_col, step):
                    if board[start_row][c]:
                        return False
                return True
            elif start_col == end_col:
                step = 1 if end_row > start_row else -1
                for r in range(start_row + step, end_row, step):
                    if board[r][start_col]:
                        return False
                return True
            elif abs(end_row - start_row) == abs(end_col - start_col):
                row_step = 1 if end_row > start_row else -1
                col_step = 1 if end_col > start_col else -1
                r, c = start_row + row_step, start_col + col_step
                while r != end_row and c != end_col:
                    if board[r][c]:
                        return False
                    r += row_step
                    c += col_step
                return True

        elif piece.type == "king":
            return abs(end_row - start_row) <= 1 and abs(end_col - start_col) <= 1

        return False

    def is_checkmate(self) -> bool:
        if not self.check:
            return False
            
        # Check if any move can get the king out of check
        for start_row in range(8):
            for start_col in range(8):
                piece = self.board[start_row][start_col]
                if piece and piece.color == self.turn:
                    for end_row in range(8):
                        for end_col in range(8):
                            if self.is_valid_move((start_row, start_col), (end_row, end_col)):
                                return False
        return True

    def is_stalemate(self) -> bool:
        if self.check:
            return False
            
        for start_row in range(8):
            for start_col in range(8):
                piece = self.board[start_row][start_col]
                if piece and piece.color == self.turn:
                    for end_row in range(8):
                        for end_col in range(8):
                            if self.is_valid_move((start_row, start_col), (end_row, end_col)):
                                return False
        return True

    def is_valid_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        if not self.is_valid_move_for_piece(start, end, self.board):
            return False
            
        piece = self.board[start[0]][start[1]]
        if not piece:
            return False

        # Make a temporary move to check if it leaves king in check
        board_copy = [row[:] for row in self.board]
        board_copy[end[0]][end[1]] = board_copy[start[0]][start[1]]
        board_copy[start[0]][start[1]] = None
        
        # Temporarily update king position if moving king
        if piece.type == "king":
            if piece.color == "white":
                temp_king_pos = self.white_king_pos
                self.white_king_pos = end
            else:
                temp_king_pos = self.black_king_pos
                self.black_king_pos = end
        else:
            temp_king_pos = None
        
        in_check = self.is_in_check(piece.color, board_copy)
        
        # Restore king position if we changed it
        if piece.type == "king":
            if piece.color == "white":
                self.white_king_pos = temp_king_pos
            else:
                self.black_king_pos = temp_king_pos
                
        return not in_check

    def move_piece(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]

        if not piece:
            return False

        # Handle knight orientation
        if piece.type == "knight":
            if end_col > start_col:
                piece.angle = 0
            else:
                piece.angle = 180

        # Move the piece
        captured_piece = self.board[end_row][end_col]
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        piece.has_moved = True

        # Update king position if moving king
        if piece.type == "king":
            if piece.color == "white":
                self.white_king_pos = (end_row, end_col)
            else:
                self.black_king_pos = (end_row, end_col)

        # Check for pawn promotion
        if piece.type == "pawn" and (end_row == 0 or end_row == 7):
            self.promoting = True
            self.promotion_pos = (end_row, end_col)
            self.promotion_buttons = []  # Reset buttons
            return True

        # Check if opponent is now in check
        opponent_color = "black" if self.turn == "white" else "white"
        self.check = self.is_in_check(opponent_color)
        
        # Check for checkmate or stalemate
        if self.check:
            self.checkmate = self.is_checkmate()
            if self.checkmate:
                self.game_over = True
                self.winner = "White" if self.turn == "black" else "Black"
        else:
            self.stalemate = self.is_stalemate()
            if self.stalemate:
                self.game_over = True
        
        # Update timers and switch turns if game isn't over
        self.update_timers()
        
        if not self.game_over and not self.promoting:
            self.turn = "black" if self.turn == "white" else "white"
            
            if self.vs_computer and self.turn == self.computer_color:
                self.computer_thinking = True
                pygame.time.set_timer(pygame.USEREVENT, 1000)
                
        self.selected_piece = None
        self.valid_moves = []
        return True

    def promote_pawn(self, piece_type: str) -> None:
        if not self.promoting or not self.promotion_pos:
            return
            
        row, col = self.promotion_pos
        piece = self.board[row][col]
        if not piece or piece.type != "pawn":
            return
            
        color = piece.color
        
        # Replace pawn with selected piece
        self.board[row][col] = Piece(color, piece_type)
        
        # Check if opponent is now in check
        opponent_color = "black" if self.turn == "white" else "white"
        self.check = self.is_in_check(opponent_color)
        
        # Check for checkmate or stalemate
        if self.check:
            self.checkmate = self.is_checkmate()
            if self.checkmate:
                self.game_over = True
                self.winner = "White" if self.turn == "black" else "Black"
        else:
            self.stalemate = self.is_stalemate()
            if self.stalemate:
                self.game_over = True
        
        # Update timers and switch turns if game isn't over
        self.update_timers()
        
        if not self.game_over:
            self.turn = "black" if self.turn == "white" else "white"
            
            if self.vs_computer and self.turn == self.computer_color:
                self.computer_thinking = True
                pygame.time.set_timer(pygame.USEREVENT, 1000)
                
        self.selected_piece = None
        self.valid_moves = []
        self.promoting = False
        self.promotion_pos = None
        self.promotion_buttons = []

    def handle_click(self, row: int, col: int):
        if self.selecting_mode or self.game_over or self.paused or self.show_settings:
            return
            
        if (self.vs_computer and self.turn == self.computer_color):
            return
            
        if self.promoting:
            # Check if promotion button was clicked
            mouse_pos = pygame.mouse.get_pos()
            for button in self.promotion_buttons:
                if button.is_clicked(mouse_pos, pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1})):
                    self.promote_pawn(button.piece_type)
                    return
            return
            
        if self.selected_piece:
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected_piece, (row, col))
            else:
                self.selected_piece = None
                self.valid_moves = []
        else:
            piece = self.board[row][col]
            if piece and piece.color == self.turn:
                self.selected_piece = (row, col)
                self.valid_moves = []
                
                # Find all valid moves for this piece
                for r in range(8):
                    for c in range(8):
                        if self.is_valid_move((row, col), (r, c)):
                            self.valid_moves.append((r, c))

    def computer_move(self):
        if self.computer_thinking:
            self.computer_thinking = False
            pygame.time.set_timer(pygame.USEREVENT, 0)
            
            possible_moves = []
            for start_row in range(8):
                for start_col in range(8):
                    piece = self.board[start_row][start_col]
                    if piece and piece.color == self.computer_color:
                        for end_row in range(8):
                            for end_col in range(8):
                                if self.is_valid_move((start_row, start_col), (end_row, end_col)):
                                    possible_moves.append(((start_row, start_col), (end_row, end_col)))
            
            if possible_moves:
                # Prefer capturing moves
                capture_moves = []
                for move in possible_moves:
                    start, end = move
                    target_piece = self.board[end[0]][end[1]]
                    if target_piece and target_piece.color != self.computer_color:
                        value = self.get_piece_value(target_piece)
                        capture_moves.append((move, value))
                
                if capture_moves:
                    capture_moves.sort(key=lambda x: -x[1])
                    selected_move = capture_moves[0][0]
                else:
                    selected_move = random.choice(possible_moves)
                
                self.move_piece(selected_move[0], selected_move[1])

    def get_piece_value(self, piece: Piece) -> int:
        values = {
            "pawn": 1,
            "knight": 3,
            "bishop": 3,
            "rook": 5,
            "queen": 9,
            "king": 0
        }
        return values.get(piece.type, 0)

    def handle_mode_selection(self, pos: Tuple[int, int], event: pygame.event.Event):
        if self.human_button.is_clicked(pos, event):
            self.selecting_mode = False
            self.vs_computer = False
        elif self.computer_button.is_clicked(pos, event):
            self.selecting_mode = False
            self.vs_computer = True
            self.computer_color = "black"

    def handle_control_buttons(self, pos: Tuple[int, int], event: pygame.event.Event):
        if self.pause_button.is_clicked(pos, event):
            self.toggle_pause()
        elif self.restart_button.is_clicked(pos, event):
            self.restart_game()
        elif self.settings_button.is_clicked(pos, event):
            self.show_settings = True

    def handle_settings_buttons(self, pos: Tuple[int, int], event: pygame.event.Event):
        if self.time_10m_button.is_clicked(pos, event):
            self.set_time_control(10)
        elif self.time_5m_button.is_clicked(pos, event):
            self.set_time_control(5)
        elif self.time_3m_button.is_clicked(pos, event):
            self.set_time_control(3)
        elif self.close_settings_button.is_clicked(pos, event):
            self.show_settings = False

    def reset_game(self):
        """Reset the game to initial state"""
        self.__init__(vs_computer=self.vs_computer, computer_color=self.computer_color)

def main():
    board = Board()
    clock = pygame.time.Clock()
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if board.selecting_mode:
                    board.handle_mode_selection(mouse_pos, event)
                elif board.show_settings:
                    board.handle_settings_buttons(mouse_pos, event)
                else:
                    # Handle control buttons
                    board.handle_control_buttons(mouse_pos, event)
                    
                    # Handle chess board clicks only if not in control panel
                    x, y = mouse_pos
                    if y < BOARD_SIZE:
                        row, col = y // SQUARE_SIZE, x // SQUARE_SIZE
                        board.handle_click(row, col)
            elif event.type == pygame.USEREVENT and board.vs_computer:
                board.computer_move()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (board.checkmate or board.stalemate or board.game_over):
                    board.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    if board.show_settings:
                        board.show_settings = False
                    else:
                        board.toggle_pause()
        
        # Update button hover states
        if board.selecting_mode:
            board.human_button.check_hover(mouse_pos)
            board.computer_button.check_hover(mouse_pos)
        elif board.show_settings:
            board.time_10m_button.check_hover(mouse_pos)
            board.time_5m_button.check_hover(mouse_pos)
            board.time_3m_button.check_hover(mouse_pos)
            board.close_settings_button.check_hover(mouse_pos)
        elif board.promoting:
            for button in board.promotion_buttons:
                button.check_hover(mouse_pos)
        else:
            board.pause_button.check_hover(mouse_pos)
            board.restart_button.check_hover(mouse_pos)
            board.settings_button.check_hover(mouse_pos)
        
        board.update_timers()

        screen.fill(WHITE)
        board.draw(screen)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()