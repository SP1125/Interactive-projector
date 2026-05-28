class Ship {
  final int id;
  final int size;
  int hitsRemaining;
  int? sunkByPlayer;
  bool horizontal = true; // set by ShipGenerator after placement
  List<List<int>> cells = []; // list of [row, col] in placement order

  Ship({required this.id, required this.size}) : hitsRemaining = size;

  bool get isSunk => hitsRemaining == 0;
}

class GameBoard {
  static const int size = 10;

  List<List<int>> board = List.generate(size, (_) => List.filled(size, 0));
  List<List<bool>> revealed = List.generate(size, (_) => List.filled(size, false));
  Map<int, Ship> ships = {};

  int get remainingShips => ships.values.where((s) => !s.isSunk).length;
}