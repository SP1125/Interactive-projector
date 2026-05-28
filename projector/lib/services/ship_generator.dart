import 'dart:math';
import '../models/game_board.dart';

class ShipGenerator {
  static final Random random = Random();

  static void placeShips(GameBoard gameBoard) {
    List<int> shipSizes = [5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2];
    int shipId = 1;

    for (int shipSize in shipSizes) {
      bool placed = false;
      int attempts = 0;
      while (!placed) {
        attempts++;
        if (attempts > 2000) {
          gameBoard.board = List.generate(10, (_) => List.filled(10, 0));
          gameBoard.ships.clear();
          shipId = 1;
          attempts = 0;
        }
        int row = random.nextInt(10);
        int col = random.nextInt(10);
        bool horizontal = random.nextBool();

        if (_canPlace(gameBoard, row, col, shipSize, horizontal)) {
          _place(gameBoard, row, col, shipSize, horizontal, shipId);
          shipId++;
          placed = true;
        }
      }
    }
  }

  static bool _canPlace(GameBoard board, int row, int col, int size, bool horizontal) {
    for (int i = 0; i < size; i++) {
      int r = horizontal ? row : row + i;
      int c = horizontal ? col + i : col;
      if (r >= 10 || c >= 10) return false;
      if (board.board[r][c] != 0) return false;
    }
    return true;
  }

  static void _place(GameBoard board, int row, int col, int size, bool horizontal, int shipId) {
    final ship = Ship(id: shipId, size: size);
    ship.horizontal = horizontal;
    for (int i = 0; i < size; i++) {
      int r = horizontal ? row : row + i;
      int c = horizontal ? col + i : col;
      board.board[r][c] = shipId;
      ship.cells.add([r, c]);
    }
    board.ships[shipId] = ship;
  }
}