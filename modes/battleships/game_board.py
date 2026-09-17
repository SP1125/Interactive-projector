# game_board.py

import random

# 14 columns, 7 rows
GRID_COLS = 14
GRID_ROWS = 7


class Ship:
    def __init__(self, ship_id: int, size: int):
        self.id = ship_id
        self.size = size
        self.hits_remaining = size
        self.sunk_by_player = None
        self.horizontal = True
        self.cells: list[tuple[int, int]] = []

    @property
    def is_sunk(self) -> bool:
        return self.hits_remaining == 0


class GameBoard:
    def __init__(self):
        self.board:    list[list[int]]  = [[0] * GRID_COLS for _ in range(GRID_ROWS)]
        self.revealed: list[list[bool]] = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
        self.ships:    dict[int, Ship]  = {}

    @property
    def remaining_ships(self) -> int:
        return sum(1 for s in self.ships.values() if not s.is_sunk)


class ShipGenerator:
    # Fleet for 14×7 = 98 cells — same original fleet as the Flutter version
    FLEET = [5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2]

    @staticmethod
    def place_ships(board: GameBoard):
        ship_id = 1
        for size in ShipGenerator.FLEET:
            placed = False
            attempts = 0
            while not placed:
                attempts += 1
                if attempts > 2000:
                    # Full restart
                    board.board    = [[0] * GRID_COLS for _ in range(GRID_ROWS)]
                    board.ships    = {}
                    ship_id = 1
                    attempts = 0
                row   = random.randint(0, GRID_ROWS - 1)
                col   = random.randint(0, GRID_COLS - 1)
                horiz = random.choice([True, False])
                if ShipGenerator._can_place(board, row, col, size, horiz):
                    ShipGenerator._place(board, row, col, size, horiz, ship_id)
                    ship_id += 1
                    placed = True

    @staticmethod
    def _can_place(board: GameBoard, row: int, col: int, size: int, horizontal: bool) -> bool:
        for i in range(size):
            r = row if horizontal else row + i
            c = col + i if horizontal else col
            if r >= GRID_ROWS or c >= GRID_COLS:
                return False
            if board.board[r][c] != 0:
                return False
        return True

    @staticmethod
    def _place(board: GameBoard, row: int, col: int, size: int, horizontal: bool, ship_id: int):
        ship = Ship(ship_id, size)
        ship.horizontal = horizontal
        for i in range(size):
            r = row if horizontal else row + i
            c = col + i if horizontal else col
            board.board[r][c] = ship_id
            ship.cells.append((r, c))
        board.ships[ship_id] = ship