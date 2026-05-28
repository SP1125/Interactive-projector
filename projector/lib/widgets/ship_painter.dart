import 'dart:math';
import 'package:flutter/material.dart';

/// Draws a top-down ship silhouette scaled to [tileSize] * [shipSize] wide.
/// Each ship size has a unique design.
class ShipIconPainter extends CustomPainter {
  final int shipSize;
  final double tileSize;
  final bool sunk;
  final Color sunkColor;

  ShipIconPainter({
    required this.shipSize,
    required this.tileSize,
    this.sunk = false,
    this.sunkColor = Colors.red,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
  final h = size.height;

    final hullPaint = Paint()
      ..color = sunk ? sunkColor.withOpacity(0.9) : const Color(0xFF37474F);
    final deckPaint = Paint()
      ..color = sunk ? sunkColor.withOpacity(0.6) : const Color(0xFF546E7A);
    final accentPaint = Paint()
      ..color = sunk ? Colors.white.withOpacity(0.4) : const Color(0xFF00BCD4).withOpacity(0.8);
    final metalPaint = Paint()
      ..color = sunk ? Colors.white.withOpacity(0.5) : const Color(0xFF78909C);

    switch (shipSize) {
      case 5:
        _drawCarrier(canvas, w, h, hullPaint, deckPaint, accentPaint, metalPaint);
        break;
      case 4:
        _drawBattleship(canvas, w, h, hullPaint, deckPaint, accentPaint, metalPaint);
        break;
      case 3:
        _drawDestroyer(canvas, w, h, hullPaint, deckPaint, accentPaint, metalPaint);
        break;
      case 2:
        _drawPatrol(canvas, w, h, hullPaint, deckPaint, accentPaint, metalPaint);
        break;
    }

    if (sunk) _drawFireOverlay(canvas, w, h);
  }

  void _drawCarrier(Canvas c, double w, double h,
      Paint hull, Paint deck, Paint accent, Paint metal) {
    // Long flat hull
    final hullPath = Path()
      ..moveTo(w * 0.04, h * 0.30)
      ..quadraticBezierTo(0, h * 0.5, w * 0.04, h * 0.70)
      ..lineTo(w * 0.96, h * 0.70)
      ..quadraticBezierTo(w, h * 0.5, w * 0.96, h * 0.30)
      ..close();
    c.drawPath(hullPath, hull);

    // Runway stripe
    c.drawRect(Rect.fromLTWH(w * 0.05, h * 0.43, w * 0.9, h * 0.14), deck);

    // Island superstructure (right side)
    c.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.62, h * 0.14, w * 0.30, h * 0.18), const Radius.circular(2)),
      deck,
    );
    // Mast
    c.drawLine(Offset(w * 0.74, h * 0.14), Offset(w * 0.74, h * 0.02),
        metal..strokeWidth = 1.5);
    // Radar dish (circle)
    c.drawCircle(Offset(w * 0.74, h * 0.05), w * 0.028,
        Paint()..color = const Color(0xFF90A4AE)..style = PaintingStyle.stroke..strokeWidth = 1);

    // Accent stripe along hull
    c.drawRect(Rect.fromLTWH(w * 0.04, h * 0.66, w * 0.92, h * 0.05), accent);
  }

  void _drawBattleship(Canvas c, double w, double h,
      Paint hull, Paint deck, Paint accent, Paint metal) {
    final hullPath = Path()
      ..moveTo(w * 0.06, h * 0.28)
      ..quadraticBezierTo(0, h * 0.5, w * 0.06, h * 0.72)
      ..lineTo(w * 0.94, h * 0.72)
      ..quadraticBezierTo(w, h * 0.5, w * 0.94, h * 0.28)
      ..close();
    c.drawPath(hullPath, hull);

    // Central bridge block
    c.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.30, h * 0.12, w * 0.40, h * 0.20), const Radius.circular(2)),
      deck,
    );
    // Funnel (tall rectangle)
    c.drawRect(Rect.fromLTWH(w * 0.44, h * 0.02, w * 0.12, h * 0.12), metal);

    // Front gun turret
    c.drawRect(Rect.fromLTWH(w * 0.06, h * 0.38, w * 0.18, h * 0.24), deck);
    // Gun barrel front
    c.drawLine(Offset(w * 0.05, h * 0.48), Offset(w * 0.0, h * 0.45),
        Paint()..color = const Color(0xFF263238)..strokeWidth = 2.5);

    // Rear gun turret
    c.drawRect(Rect.fromLTWH(w * 0.76, h * 0.38, w * 0.18, h * 0.24), deck);
    c.drawLine(Offset(w * 0.95, h * 0.48), Offset(w, h * 0.45),
        Paint()..color = const Color(0xFF263238)..strokeWidth = 2.5);

    // Accent stripe
    c.drawRect(Rect.fromLTWH(w * 0.06, h * 0.68, w * 0.88, h * 0.05), accent);
  }

  void _drawDestroyer(Canvas c, double w, double h,
      Paint hull, Paint deck, Paint accent, Paint metal) {
    // Sleeker hull, pointed bow
    final hullPath = Path()
      ..moveTo(w * 0.02, h * 0.32)
      ..quadraticBezierTo(0, h * 0.50, w * 0.04, h * 0.68)
      ..lineTo(w * 0.96, h * 0.68)
      ..quadraticBezierTo(w, h * 0.50, w * 0.98, h * 0.32)
      ..close();
    c.drawPath(hullPath, hull);

    // Bridge — offset forward
    c.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.20, h * 0.14, w * 0.35, h * 0.20), const Radius.circular(3)),
      deck,
    );
    // Tall mast
    c.drawLine(Offset(w * 0.33, h * 0.14), Offset(w * 0.33, h * 0.0),
        metal..strokeWidth = 1.5);
    // Crossbar
    c.drawLine(Offset(w * 0.24, h * 0.04), Offset(w * 0.42, h * 0.04),
        metal..strokeWidth = 1.0);

    // Torpedo tubes (rear)
    c.drawRect(Rect.fromLTWH(w * 0.62, h * 0.40, w * 0.28, h * 0.18), deck);

    // Accent stripe
    c.drawRect(Rect.fromLTWH(w * 0.04, h * 0.64, w * 0.92, h * 0.05), accent);
  }

  void _drawPatrol(Canvas c, double w, double h,
      Paint hull, Paint deck, Paint accent, Paint metal) {
    // Small rounded hull
    final hullPath = Path()
      ..moveTo(w * 0.08, h * 0.35)
      ..quadraticBezierTo(0, h * 0.5, w * 0.08, h * 0.65)
      ..lineTo(w * 0.92, h * 0.65)
      ..quadraticBezierTo(w, h * 0.5, w * 0.92, h * 0.35)
      ..close();
    c.drawPath(hullPath, hull);

    // Wheelhouse
    c.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(w * 0.20, h * 0.20, w * 0.40, h * 0.18), const Radius.circular(3)),
      deck,
    );
    // Short antenna
    c.drawLine(Offset(w * 0.35, h * 0.20), Offset(w * 0.35, h * 0.06),
        metal..strokeWidth = 1.2);

    // Accent
    c.drawRect(Rect.fromLTWH(w * 0.08, h * 0.61, w * 0.84, h * 0.05), accent);
  }

  void _drawFireOverlay(Canvas canvas, double w, double h) {
    final rng = Random(shipSize * 31 + 7);
    final positions = [0.2, 0.5, 0.8];
    for (final xFrac in positions) {
      final fx = w * (xFrac + (rng.nextDouble() - 0.5) * 0.12);
      _flame(canvas, fx, h * 0.72, w * 0.12, h * 0.38,
          Paint()..color = const Color(0xFFFFE082).withOpacity(0.9));
      _flame(canvas, fx + w * 0.07, h * 0.72, w * 0.08, h * 0.26,
          Paint()..color = const Color(0xFFFF6F00).withOpacity(0.8));
    }
    // Smoke
    final smokePaint = Paint()
      ..color = Colors.white.withOpacity(0.10)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    for (final xFrac in [0.25, 0.55, 0.78]) {
      final sx = w * xFrac;
      final path = Path()
        ..moveTo(sx, h * 0.05)
        ..quadraticBezierTo(sx + 5, 0, sx - 4, -h * 0.08);
      canvas.drawPath(path, smokePaint);
    }
  }

  void _flame(Canvas canvas, double cx, double baseY, double fw, double fh, Paint paint) {
    final path = Path()
      ..moveTo(cx, baseY)
      ..quadraticBezierTo(cx - fw, baseY - fh * 0.5, cx - fw * 0.3, baseY - fh * 0.85)
      ..quadraticBezierTo(cx, baseY - fh, cx + fw * 0.3, baseY - fh * 0.85)
      ..quadraticBezierTo(cx + fw, baseY - fh * 0.5, cx, baseY);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(ShipIconPainter old) =>
      old.shipSize != shipSize || old.sunk != sunk;
}