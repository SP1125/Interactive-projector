import 'dart:math';
import 'package:flutter/material.dart';

// value: 0=unrevealed-ocean  2=hit(alive)  3=miss  4=sunk-p1  5=sunk-p2

class GridTileWidget extends StatelessWidget {
  final int value;
  final VoidCallback onTap;
  final int shipSize;
  final int tileIndex;
  final bool isHorizontal;
  final int col;
  final int row;

  const GridTileWidget({
    super.key,
    required this.value,
    required this.onTap,
    this.shipSize = 1,
    this.tileIndex = 0,
    this.isHorizontal = true,
    this.col = 0,
    this.row = 0,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        child: _buildTileContent(),
      ),
    );
  }

  Widget _buildTileContent() {
    switch (value) {
      // ── HIT (ship alive) — orange bg + fire icon ──────────────────────────
      case 2:
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFFE65100),
            border: Border.fromBorderSide(
              BorderSide(color: Color(0xFFFFAB00), width: 1.2),
            ),
          ),
          child: const Center(
            child: Icon(
              Icons.local_fire_department,
              color: Color(0xFFFFFFFF),
              size: 16,
            ),
          ),
        );

      // ── MISS — dark ocean + bold X cross ─────────────────────────────────
      case 3:
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0D1F2E),
            border: Border.fromBorderSide(
              BorderSide(color: Color(0xFF1E3A50), width: 1.2),
            ),
          ),
          child: Center(
            child: CustomPaint(
              painter: _CrossPainter(),
              size: const Size(10, 10),
            ),
          ),
        );

      // ── SUNK tiles — use CustomPaint for ship silhouette + fire ───────────
      case 4:
      case 5:
        return CustomPaint(
          painter: _TilePainter(
            value: value,
            shipSize: shipSize,
            tileIndex: tileIndex,
            isHorizontal: isHorizontal,
            gridCol: col,
            gridRow: row,
          ),
        );

      // ── UNREVEALED — animated ocean (CustomPaint) ─────────────────────────
      default:
        return CustomPaint(
          painter: _TilePainter(
            value: 0,
            shipSize: shipSize,
            tileIndex: tileIndex,
            isHorizontal: isHorizontal,
            gridCol: col,
            gridRow: row,
          ),
        );
    }
  }
}

// ── Bold X cross for miss ─────────────────────────────────────────────────────
class _CrossPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF80D8FF)
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(Offset(0, 0), Offset(size.width, size.height), paint);
    canvas.drawLine(Offset(size.width, 0), Offset(0, size.height), paint);
  }
  @override
  bool shouldRepaint(_CrossPainter _) => false;
}

// ── Tile Painter (ocean + sunk only) ─────────────────────────────────────────
class _TilePainter extends CustomPainter {
  final int value;
  final int shipSize;
  final int tileIndex;
  final bool isHorizontal;
  final int gridCol;
  final int gridRow;

  _TilePainter({
    required this.value,
    required this.shipSize,
    required this.tileIndex,
    required this.isHorizontal,
    required this.gridCol,
    required this.gridRow,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final rect = Rect.fromLTWH(0, 0, w, h);

    if (value == 0) {
      _paintOcean(canvas, rect, w, h);
    } else {
      _paintSunk(canvas, rect, w, h, value == 4 ? const Color(0xFFCC0000) : const Color(0xFF0033CC));
    }

    // Border
    final borderColor = value == 0
        ? const Color(0xFF00BCD4)
        : value == 3 ? const Color(0xFF1E3A50) : Colors.black38;
    canvas.drawRect(
      rect.deflate(0.6),
      Paint()
        ..color = borderColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );
  }

  void _paintOcean(Canvas canvas, Rect rect, double w, double h) {
    final depthT = gridRow / 9.0;
    final baseColor = Color.lerp(
      const Color(0xFF0A2A3F),
      const Color(0xFF020E1A),
      depthT,
    )!;
    canvas.drawRect(rect, Paint()..color = baseColor);

    final phase = gridCol * 0.7 + gridRow * 0.4;
    final shimmerPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFF00BCD4).withOpacity(0.0),
          const Color(0xFF00BCD4).withOpacity(0.07 + 0.04 * sin(phase * 1.3)),
          const Color(0xFF00BCD4).withOpacity(0.0),
        ],
        stops: const [0.0, 0.5, 1.0],
      ).createShader(rect);
    canvas.drawRect(rect, shimmerPaint);

    final shimmerY = h * (0.3 + 0.25 * sin(phase));
    final wavePath = Path()..moveTo(0, shimmerY);
    for (double x = 0; x <= w; x += 1) {
      wavePath.lineTo(x, shimmerY + 1.5 * sin(x / w * pi * 2 + phase));
    }
    canvas.drawPath(wavePath,
        Paint()
          ..color = const Color(0xFF00E5FF).withOpacity(0.12)
          ..strokeWidth = 0.8
          ..style = PaintingStyle.stroke);

    final specX = w * ((sin(phase * 3.7) * 0.5 + 0.5) * 0.6 + 0.2);
    final specY = h * ((cos(phase * 2.3) * 0.5 + 0.5) * 0.4 + 0.1);
    canvas.drawCircle(Offset(specX, specY), 0.9,
        Paint()..color = const Color(0xFF80DEEA).withOpacity(0.35));
  }

  void _paintSunk(Canvas canvas, Rect rect, double w, double h, Color playerColor) {
    canvas.drawRect(
      rect,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [playerColor.withOpacity(0.7), playerColor.withOpacity(0.9)],
        ).createShader(rect),
    );

    _drawShipSegment(canvas, w, h, playerColor);

    // Fire icons rendered as drawn flames
    final rng = Random(gridRow * 10 + gridCol);
    final fx = w * (0.2 + rng.nextDouble() * 0.6);
    _drawFlame(canvas, fx, h * 0.85, w * 0.22, h * 0.45,
        Paint()..color = const Color(0xFFFFE082).withOpacity(0.9));
    _drawFlame(canvas, w - fx, h * 0.85, w * 0.16, h * 0.32,
        Paint()..color = const Color(0xFFFF6F00).withOpacity(0.7));

    final smokePaint = Paint()
      ..color = Colors.white.withOpacity(0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    final sx = w * (0.3 + rng.nextDouble() * 0.4);
    canvas.drawPath(
      Path()..moveTo(sx, 0)..quadraticBezierTo(sx + 4, h * 0.15, sx - 3, h * 0.3),
      smokePaint,
    );
  }

  void _drawShipSegment(Canvas canvas, double w, double h, Color playerColor) {
    final isBow   = tileIndex == 0;
    final isStern = tileIndex == shipSize - 1;

    final hullPaint  = Paint()..color = const Color(0xFF1A1A1A);
    final deckPaint  = Paint()..color = const Color(0xFF2A2A2A);
    final accentPaint = Paint()..color = playerColor.withOpacity(0.6);
    final metalPaint = Paint()..color = const Color(0xFF444444);

    if (!isHorizontal) {
      canvas.save();
      canvas.translate(w / 2, h / 2);
      canvas.rotate(pi / 2);
      canvas.translate(-h / 2, -w / 2);
      _drawHorizontalSegment(canvas, h, w, isBow, isStern, hullPaint, deckPaint, accentPaint, metalPaint);
      canvas.restore();
    } else {
      _drawHorizontalSegment(canvas, w, h, isBow, isStern, hullPaint, deckPaint, accentPaint, metalPaint);
    }
  }

  void _drawHorizontalSegment(
    Canvas canvas, double w, double h,
    bool isBow, bool isStern,
    Paint hullPaint, Paint deckPaint, Paint accentPaint, Paint metalPaint,
  ) {
    final deckTop = h * 0.28;
    final deckBot = h * 0.72;
    final hullBot = h * 0.82;

    switch (shipSize) {
      case 5:
        _drawHullSection(canvas, w, h, isBow, isStern, deckTop, deckBot, hullBot, hullPaint);
        canvas.drawRect(Rect.fromLTWH(0, h * 0.44, w, h * 0.12), Paint()..color = const Color(0xFF555555));
        if (isBow) {
          canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w*0.1, deckTop-h*0.22, w*0.35, h*0.22), const Radius.circular(2)), deckPaint);
          canvas.drawRect(Rect.fromLTWH(w*0.18, deckTop-h*0.34, w*0.08, h*0.14), metalPaint);
        }
        if (tileIndex == 2) {
          canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w*0.2, deckTop-h*0.28, w*0.6, h*0.28), const Radius.circular(2)), deckPaint);
          canvas.drawRect(Rect.fromLTWH(w*0.38, deckTop-h*0.44, w*0.1, h*0.18), metalPaint);
        }
        canvas.drawRect(Rect.fromLTWH(0, h*0.68, w, h*0.05), accentPaint);
        break;

      case 4:
        _drawHullSection(canvas, w, h, isBow, isStern, deckTop, deckBot, hullBot, hullPaint);
        if (isBow) {
          canvas.drawRect(Rect.fromLTWH(w*0.1, deckTop, w*0.7, h*0.22), deckPaint);
          canvas.drawRect(Rect.fromLTWH(w*0.3, deckTop-h*0.12, w*0.08, h*0.16), metalPaint);
        }
        if (tileIndex == 1) {
          canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w*0.1, deckTop-h*0.30, w*0.8, h*0.30), const Radius.circular(2)), deckPaint);
          canvas.drawRect(Rect.fromLTWH(w*0.35, deckTop-h*0.48, w*0.12, h*0.2), metalPaint);
        }
        if (isStern) {
          canvas.drawRect(Rect.fromLTWH(w*0.1, deckTop, w*0.7, h*0.18), deckPaint);
          canvas.drawRect(Rect.fromLTWH(w*0.4, deckTop-h*0.10, w*0.08, h*0.14), metalPaint);
        }
        canvas.drawRect(Rect.fromLTWH(0, h*0.68, w, h*0.05), accentPaint);
        break;

      case 3:
        _drawHullSection(canvas, w, h, isBow, isStern, h*0.32, h*0.68, h*0.80, hullPaint);
        if (tileIndex == 1) {
          canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w*0.15, h*0.10, w*0.7, h*0.22), const Radius.circular(3)), deckPaint);
          canvas.drawLine(Offset(w*0.5, h*0.10), Offset(w*0.5, 0),
              metalPaint..strokeWidth = 1.5);
        }
        canvas.drawRect(Rect.fromLTWH(0, h*0.64, w, h*0.04), accentPaint);
        break;

      case 2:
        _drawHullSection(canvas, w, h, isBow, isStern, h*0.35, h*0.65, h*0.78, hullPaint);
        if (isBow) {
          canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w*0.15, h*0.18, w*0.7, h*0.18), const Radius.circular(3)), deckPaint);
        }
        canvas.drawRect(Rect.fromLTWH(0, h*0.62, w, h*0.04), accentPaint);
        break;

      default:
        _drawHullSection(canvas, w, h, isBow, isStern, deckTop, deckBot, hullBot, hullPaint);
    }
  }

  void _drawHullSection(Canvas canvas, double w, double h, bool isBow, bool isStern,
      double deckTop, double deckBot, double hullBot, Paint hullPaint) {
    final path = Path();
    if (isBow && isStern) {
      path.moveTo(w*0.1, deckTop);
      path.lineTo(w*0.9, deckTop);
      path.lineTo(w*0.95, deckBot);
      path.lineTo(w*0.05, deckBot);
      path.close();
    } else if (isBow) {
      path.moveTo(w*0.05, deckTop);
      path.quadraticBezierTo(0, deckBot, w*0.05, hullBot);
      path.lineTo(w, hullBot);
      path.lineTo(w, deckTop);
      path.close();
    } else if (isStern) {
      path.moveTo(0, deckTop);
      path.lineTo(0, hullBot);
      path.lineTo(w*0.95, hullBot);
      path.quadraticBezierTo(w, deckBot, w*0.9, deckTop);
      path.close();
    } else {
      path.addRect(Rect.fromLTWH(0, deckTop, w, hullBot - deckTop));
    }
    canvas.drawPath(path, hullPaint);
  }

  void _drawFlame(Canvas canvas, double cx, double baseY, double fw, double fh, Paint paint) {
    final path = Path()
      ..moveTo(cx, baseY)
      ..quadraticBezierTo(cx-fw, baseY-fh*0.5, cx-fw*0.3, baseY-fh*0.8)
      ..quadraticBezierTo(cx, baseY-fh, cx+fw*0.3, baseY-fh*0.8)
      ..quadraticBezierTo(cx+fw, baseY-fh*0.5, cx, baseY);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_TilePainter old) =>
      old.value != value || old.shipSize != shipSize ||
      old.tileIndex != tileIndex || old.isHorizontal != isHorizontal;
}