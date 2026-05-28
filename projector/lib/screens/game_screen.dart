import 'dart:math';
import 'package:flutter/material.dart';

import '../models/game_board.dart';
import '../services/ship_generator.dart';
import '../widgets/grid_tile.dart';
import '../widgets/ship_painter.dart';

class GameScreen extends StatefulWidget {
  const GameScreen({super.key});

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> with SingleTickerProviderStateMixin {
  late GameBoard gameBoard;
  int currentPlayer = 1;
  int player1Score = 0;
  int player2Score = 0;
  int roundNumber = 1;

  late AnimationController _bgController;

  static const Color p1Color    = Color(0xFFFF1744);
  static const Color p2Color    = Color(0xFF2979FF);
  static const Color accentCyan = Color(0xFF00E5FF);

  @override
  void initState() {
    super.initState();
    _bgController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();
    _newBoard();
  }

  @override
  void dispose() {
    _bgController.dispose();
    super.dispose();
  }

  void _newBoard() {
    gameBoard = GameBoard();
    ShipGenerator.placeShips(gameBoard);
  }

  void handleTap(int row, int col) {
    if (gameBoard.revealed[row][col]) return;

    setState(() {
      gameBoard.revealed[row][col] = true;
      final cellValue = gameBoard.board[row][col];

      if (cellValue != 0) {
        final ship = gameBoard.ships[cellValue]!;
        ship.hitsRemaining--;

        if (ship.isSunk) {
          ship.sunkByPlayer = currentPlayer;
          for (final cell in ship.cells) {
            gameBoard.revealed[cell[0]][cell[1]] = true;
          }
          if (currentPlayer == 1) player1Score++; else player2Score++;

          if (gameBoard.remainingShips == 0) {
            _showRoundEndDialog();
          } else {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text(
                '💥  PLAYER $currentPlayer SANK A ${ship.size}-TILE SHIP!  +1 POINT',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, letterSpacing: 1),
              ),
              duration: const Duration(seconds: 3),
              backgroundColor: currentPlayer == 1 ? p1Color : p2Color,
            ));
          }
        }
      } else {
        currentPlayer = currentPlayer == 1 ? 2 : 1;
      }
    });
  }

  void _showRoundEndDialog() {
    final roundWinner = currentPlayer;
    final winnerColor = roundWinner == 1 ? p1Color : p2Color;

    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withOpacity(0.92),
      builder: (_) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 36),
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: winnerColor, width: 3),
            boxShadow: [BoxShadow(color: winnerColor.withOpacity(0.5), blurRadius: 50, spreadRadius: 4)],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('ROUND $roundNumber COMPLETE',
                  style: const TextStyle(color: accentCyan, fontSize: 14, letterSpacing: 5, fontWeight: FontWeight.w700)),
              const SizedBox(height: 20),
              const Text('🏆', style: TextStyle(fontSize: 52)),
              const SizedBox(height: 8),
              Text('PLAYER $roundWinner',
                  style: TextStyle(color: winnerColor, fontSize: 52, fontWeight: FontWeight.w900, letterSpacing: 4, height: 1.0)),
              Text('WINS THE ROUND!',
                  style: TextStyle(color: winnerColor.withOpacity(0.8), fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: 3)),
              const SizedBox(height: 28),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.04),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.white12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Column(children: [
                      const Text('PLAYER 1', style: TextStyle(color: p1Color, fontSize: 13, letterSpacing: 3, fontWeight: FontWeight.bold)),
                      Text('$player1Score', style: const TextStyle(color: p1Color, fontSize: 56, fontWeight: FontWeight.w900, height: 1.0)),
                    ]),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 28),
                      child: Text(':', style: TextStyle(color: Colors.white24, fontSize: 48, fontWeight: FontWeight.w100)),
                    ),
                    Column(children: [
                      const Text('PLAYER 2', style: TextStyle(color: p2Color, fontSize: 13, letterSpacing: 3, fontWeight: FontWeight.bold)),
                      Text('$player2Score', style: const TextStyle(color: p2Color, fontSize: 56, fontWeight: FontWeight.w900, height: 1.0)),
                    ]),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              Row(children: [
                Expanded(flex: 3, child: _dialogButton(
                  label: 'NEXT ROUND', sublabel: 'Keep scores',
                  icon: Icons.refresh_rounded, color: winnerColor,
                  onTap: () {
                    Navigator.pop(context);
                    setState(() { roundNumber++; _newBoard(); currentPlayer = roundWinner; });
                  },
                )),
                const SizedBox(width: 12),
                Expanded(flex: 2, child: _dialogButton(
                  label: 'RESET', sublabel: 'Clear scores',
                  icon: Icons.replay_rounded, color: Colors.white38,
                  onTap: () {
                    Navigator.pop(context);
                    setState(() { player1Score = 0; player2Score = 0; roundNumber = 1; currentPlayer = 1; _newBoard(); });
                  },
                )),
              ]),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dialogButton({
    required String label, required String sublabel,
    required IconData icon, required Color color, required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.withOpacity(0.6), width: 1.5),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, color: color, size: 26),
          const SizedBox(height: 6),
          Text(label, style: TextStyle(
            color: color == Colors.white38 ? Colors.white60 : color,
            fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 2)),
          Text(sublabel, style: const TextStyle(color: Colors.white30, fontSize: 10, letterSpacing: 1)),
        ]),
      ),
    );
  }

  (int, int, int, bool) _tileInfo(int row, int col) {
    if (!gameBoard.revealed[row][col]) return (0, 1, 0, true);
    final shipId = gameBoard.board[row][col];
    if (shipId == 0) return (3, 1, 0, true);
    final ship = gameBoard.ships[shipId]!;
    final idx = ship.cells.indexWhere((c) => c[0] == row && c[1] == col);
    if (!ship.isSunk) return (2, ship.size, idx, ship.horizontal);
    return (ship.sunkByPlayer == 1 ? 4 : 5, ship.size, idx, ship.horizontal);
  }

  // ── Fleet status: one ship icon per unique size + ×count ──────────────────
  Widget _buildFleet() {
    // Count remaining per size
    final Map<int, int> totalPerSize   = {};
    final Map<int, int> sunkPerSize    = {};
    for (final ship in gameBoard.ships.values) {
      totalPerSize[ship.size] = (totalPerSize[ship.size] ?? 0) + 1;
      if (ship.isSunk) sunkPerSize[ship.size] = (sunkPerSize[ship.size] ?? 0) + 1;
    }

    final sizes = totalPerSize.keys.toList()..sort((a, b) => b.compareTo(a));
    const double iconH = 28.0; // height of each ship icon

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text(
          'FLEET STATUS',
          style: TextStyle(fontSize: 11, color: Colors.white38, letterSpacing: 4, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: sizes.map((size) {
            final total  = totalPerSize[size]!;
            final sunk   = sunkPerSize[size] ?? 0;
            final remaining = total - sunk;
            final allSunk   = remaining == 0;

            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Ship icon — greyed out if all sunk
                  Opacity(
                    opacity: allSunk ? 0.3 : 1.0,
                    child: CustomPaint(
                      painter: ShipIconPainter(
                        shipSize: size,
                        tileSize: iconH,
                        sunk: false, // always show intact silhouette in fleet; fire is on the grid
                        sunkColor: Colors.transparent,
                      ),
                      size: Size(iconH * size, iconH),
                    ),
                  ),
                  const SizedBox(height: 5),
                  // Count badge
                  Text(
                    allSunk ? 'SUNK' : '×$remaining',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1,
                      color: allSunk
                          ? Colors.white24
                          : accentCyan,
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final gridSize    = screenWidth * 0.40;
    final p1Active    = currentPlayer == 1;
    final activeColor = p1Active ? p1Color : p2Color;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [

          // ── FULL-SCREEN ANIMATED OCEAN BACKGROUND ──────────────────────────
          AnimatedBuilder(
            animation: _bgController,
            builder: (_, __) => CustomPaint(
              painter: _OceanBgPainter(_bgController.value),
            ),
          ),

          // ── CONTENT ────────────────────────────────────────────────────────
          SafeArea(
            child: Column(
              children: [

                // SCOREBOARD
                Padding(
                  padding: const EdgeInsets.fromLTRB(10, 10, 10, 0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(child: _playerCard('PLAYER 1', player1Score, p1Color, p1Active)),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('ROUND',
                                style: TextStyle(color: Colors.white30, fontSize: 10, letterSpacing: 4, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 2),
                            Text('$roundNumber',
                                style: const TextStyle(color: Colors.white54, fontSize: 26, fontWeight: FontWeight.w900, height: 1.0)),
                          ],
                        ),
                      ),
                      Expanded(child: _playerCard('PLAYER 2', player2Score, p2Color, !p1Active)),
                    ],
                  ),
                ),

                const SizedBox(height: 8),

                // TURN BANNER
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.symmetric(horizontal: 10),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: activeColor.withOpacity(0.18),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: activeColor, width: 2),
                    boxShadow: [BoxShadow(color: activeColor.withOpacity(0.35), blurRadius: 16)],
                  ),
                  child: Text(
                    '▶  PLAYER $currentPlayer\'S TURN  —  TAP A SQUARE',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: activeColor, fontSize: 17, fontWeight: FontWeight.w900, letterSpacing: 3),
                  ),
                ),

                const SizedBox(height: 6),

                // GRID — with cyan glow border
                Center(
                  child: Container(
                    width: gridSize,
                    height: gridSize,
                    decoration: BoxDecoration(
                      border: Border.all(color: accentCyan.withOpacity(0.6), width: 2),
                      boxShadow: [
                        BoxShadow(color: accentCyan.withOpacity(0.20), blurRadius: 28, spreadRadius: 4),
                        BoxShadow(color: accentCyan.withOpacity(0.08), blurRadius: 60, spreadRadius: 10),
                      ],
                    ),
                    child: GridView.builder(
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: 100,
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 10),
                      itemBuilder: (context, index) {
                        final r = index ~/ 10;
                        final c = index % 10;
                        final (val, sz, idx, horiz) = _tileInfo(r, c);
                        return GridTileWidget(
                          value: val, shipSize: sz, tileIndex: idx,
                          isHorizontal: horiz, row: r, col: c,
                          onTap: () => handleTap(r, c),
                        );
                      },
                    ),
                  ),
                ),

                const SizedBox(height: 10),

                // FLEET STATUS
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: _buildFleet(),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 4),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _playerCard(String label, int score, Color color, bool isActive) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: isActive ? color.withOpacity(0.15) : Colors.black.withOpacity(0.5),
        border: Border.all(color: isActive ? color : Colors.white12, width: 2),
        boxShadow: isActive ? [BoxShadow(color: color.withOpacity(0.35), blurRadius: 14)] : [],
      ),
      child: Column(children: [
        Text(label, style: TextStyle(
          color: isActive ? color : Colors.white24,
          fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 3)),
        Text('$score', style: TextStyle(
          color: isActive ? color : Colors.white24,
          fontSize: 40, fontWeight: FontWeight.w900, height: 1.0)),
      ]),
    );
  }
}

// ── Full-screen animated ocean background ─────────────────────────────────────

class _OceanBgPainter extends CustomPainter {
  final double t;
  _OceanBgPainter(this.t);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // Deep ocean gradient sky → water
    canvas.drawRect(
      Rect.fromLTWH(0, 0, w, h),
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0xFF020810), // near-black sky
            Color(0xFF030F1C), // dark navy upper
            Color(0xFF041525), // deep ocean mid
            Color(0xFF020C18), // abyss bottom
          ],
          stops: [0.0, 0.25, 0.6, 1.0],
        ).createShader(Rect.fromLTWH(0, 0, w, h)),
    );

    // Stars
    final rng = Random(42);
    for (int i = 0; i < 40; i++) {
      final sx = rng.nextDouble() * w;
      final sy = rng.nextDouble() * h * 0.35;
      final sr = rng.nextDouble() * 1.2 + 0.3;
      final opacity = 0.2 + 0.5 * sin(t * 2 * pi * (0.4 + i * 0.07) + i).abs();
      canvas.drawCircle(Offset(sx, sy),
          sr, Paint()..color = Colors.white.withOpacity(opacity));
    }

    // Distant horizon shimmer
    final horizonY = h * 0.42;
    canvas.drawRect(
      Rect.fromLTWH(0, horizonY - 1, w, 2),
      Paint()
        ..shader = LinearGradient(
          colors: [
            Colors.transparent,
            const Color(0xFF00BCD4).withOpacity(0.25),
            const Color(0xFF00E5FF).withOpacity(0.35),
            const Color(0xFF00BCD4).withOpacity(0.25),
            Colors.transparent,
          ],
        ).createShader(Rect.fromLTWH(0, horizonY, w, 2)),
    );

    // Multiple animated wave bands
    _wave(canvas, w, h, t, 0.44, const Color(0xFF041E30), amp: 14, freq: 1.1);
    _wave(canvas, w, h, t, 0.48, const Color(0xFF051E2E), amp: 11, freq: 1.6, off: 0.4);
    _wave(canvas, w, h, t, 0.52, const Color(0xFF041826), amp: 9,  freq: 2.0, off: 0.9);
    _wave(canvas, w, h, t, 0.57, const Color(0xFF031420), amp: 7,  freq: 1.4, off: 1.5);
    _wave(canvas, w, h, t, 0.62, const Color(0xFF020E18), amp: 5,  freq: 1.8, off: 2.1);
    _wave(canvas, w, h, t, 0.68, const Color(0xFF020A14), amp: 4,  freq: 2.3, off: 0.7);
    _wave(canvas, w, h, t, 0.75, const Color(0xFF010810), amp: 3,  freq: 1.2, off: 1.8);
    _wave(canvas, w, h, t, 0.85, const Color(0xFF010609), amp: 2,  freq: 1.5, off: 0.3);

    // Cyan wave shimmer lines (on top)
    for (int i = 0; i < 4; i++) {
      final yFrac = 0.45 + i * 0.055;
      final baseY = h * yFrac;
      final phase = t * 2 * pi + i * 0.8;
      final wavePath = Path()..moveTo(0, baseY);
      for (double x = 0; x <= w; x += 2) {
        wavePath.lineTo(x, baseY + 3 * sin(x / w * pi * 3 + phase));
      }
      canvas.drawPath(
        wavePath,
        Paint()
          ..color = const Color(0xFF00E5FF).withOpacity(0.04 + 0.03 * sin(phase + i).abs())
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0,
      );
    }

    // Distant ship silhouette on horizon
    final shipY = horizonY - 18;
    final shipPaint = Paint()..color = const Color(0xFF0A1E2E);
    final shipPath = Path()
      ..moveTo(w * 0.55, shipY + 18)
      ..lineTo(w * 0.58, shipY + 8)
      ..lineTo(w * 0.78, shipY + 8)
      ..lineTo(w * 0.82, shipY + 18)
      ..close();
    canvas.drawPath(shipPath, shipPaint);
    // Bridge
    canvas.drawRect(Rect.fromLTWH(w * 0.63, shipY, w * 0.10, shipY + 8 - shipY), shipPaint);
    // Tower
    canvas.drawRect(Rect.fromLTWH(w * 0.665, shipY - 12, w * 0.03, 12), shipPaint);

    // Reflection streak on water
    final reflectPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFF00E5FF).withOpacity(0.06),
          const Color(0xFF00E5FF).withOpacity(0.0),
        ],
      ).createShader(Rect.fromLTWH(w * 0.62, horizonY, w * 0.10, h * 0.15));
    canvas.drawRect(Rect.fromLTWH(w * 0.65, horizonY, w * 0.04, h * 0.15), reflectPaint);

    // Searchlight beam — sweeps slowly
    final beamAngle = sin(t * 2 * pi * 0.3) * 0.18;
    canvas.save();
    canvas.translate(w * 0.68, shipY);
    canvas.rotate(beamAngle);
    canvas.drawPath(
      Path()
        ..moveTo(-2, 0)
        ..lineTo(-w * 0.12, -h * 0.38)
        ..lineTo(w * 0.12, -h * 0.38)
        ..lineTo(2, 0)
        ..close(),
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            Colors.white.withOpacity(0.06),
            Colors.white.withOpacity(0.0),
          ],
        ).createShader(Rect.fromLTWH(-w * 0.12, -h * 0.38, w * 0.24, h * 0.38)),
    );
    canvas.restore();
  }

  void _wave(Canvas canvas, double w, double h, double t, double yFrac, Color color,
      {double amp = 10, double freq = 1, double off = 0}) {
    final paint = Paint()..color = color;
    final path  = Path();
    final baseY = h * yFrac;
    path.moveTo(0, baseY);
    for (double x = 0; x <= w; x += 2) {
      path.lineTo(x, baseY + amp * sin(x / w * 2 * pi * freq + t * 2 * pi + off));
    }
    path.lineTo(w, h);
    path.lineTo(0, h);
    path.close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_OceanBgPainter old) => old.t != t;
}