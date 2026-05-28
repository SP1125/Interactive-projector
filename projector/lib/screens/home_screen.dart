import 'package:flutter/material.dart';
import 'dart:math';

// Projector-on-wood home screen:
// • Pure black background — wood grain shows through projected black, giving texture for free
// • All decorative elements use high-saturation cyan/amber/red — these project vividly onto wood
// • Title uses stark white + cyan glow — maximum contrast against the dark wood
// • Button is large (72px tall) with a strong glow so it's tappable from any angle
// • Subtitles & labels are larger than a normal phone UI

class HomeScreen extends StatefulWidget {
  final VoidCallback onPlay;
  const HomeScreen({super.key, required this.onPlay});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  late AnimationController _waveController;
  late AnimationController _pulseController;
  late AnimationController _titleController;
  late Animation<double> _titleAnim;
  late Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();

    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    _titleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _titleAnim = CurvedAnimation(parent: _titleController, curve: Curves.easeOutBack);
    _pulseAnim = Tween<double>(begin: 1.0, end: 1.05).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _titleController.forward();
  }

  @override
  void dispose() {
    _waveController.dispose();
    _pulseController.dispose();
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [

          // === BACKGROUND: pure black — projector black = wood texture shows through ===
          Container(color: Colors.black),

          // === ANIMATED OCEAN WAVES at bottom ===
          AnimatedBuilder(
            animation: _waveController,
            builder: (_, __) => CustomPaint(
              painter: _OceanPainter(_waveController.value),
              size: Size(size.width, size.height),
            ),
          ),

          // === STARS — bright white dots, very visible on projection ===
          ...List.generate(25, (i) {
            final rand = Random(i * 17 + 3);
            final x = rand.nextDouble() * size.width;
            final y = rand.nextDouble() * size.height * 0.42;
            final s = rand.nextDouble() * 2.5 + 1.0;
            return Positioned(
              left: x, top: y,
              child: AnimatedBuilder(
                animation: _pulseController,
                builder: (_, __) {
                  final opacity = 0.4 + 0.5 * sin(_pulseController.value * pi + i * 1.1).abs();
                  return Opacity(
                    opacity: opacity,
                    child: Container(
                      width: s, height: s,
                      decoration: const BoxDecoration(shape: BoxShape.circle, color: Colors.white),
                    ),
                  );
                },
              ),
            );
          }),

          // === HORIZON GLOW — amber/orange line at the waterline ===
          Positioned(
            bottom: size.height * 0.29,
            left: 0, right: 0,
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (_, __) {
                return Container(
                  height: 2,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.transparent,
                        const Color(0xFFFF6F00).withOpacity(0.5 + 0.2 * _pulseAnim.value),
                        const Color(0xFFFFAB00).withOpacity(0.7 + 0.2 * _pulseAnim.value),
                        const Color(0xFFFF6F00).withOpacity(0.5 + 0.2 * _pulseAnim.value),
                        Colors.transparent,
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          // === BATTLESHIP SILHOUETTE ===
          Positioned(
            bottom: size.height * 0.27,
            left: 0, right: 0,
            child: AnimatedBuilder(
              animation: _waveController,
              builder: (_, __) {
                final bob = sin(_waveController.value * 2 * pi) * 4.0;
                return Transform.translate(
                  offset: Offset(0, bob),
                  child: CustomPaint(
                    size: Size(size.width, 140),
                    painter: _ShipSilhouettePainter(),
                  ),
                );
              },
            ),
          ),

          // === EXPLOSION GLOW — orange/red, vivid on wood ===
          Positioned(
            bottom: size.height * 0.23,
            left: size.width * 0.04,
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (_, __) {
                final v = _pulseAnim.value;
                return Container(
                  width: 100, height: 100,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(colors: [
                      const Color(0xFFFF6D00).withOpacity(0.7 * v),
                      const Color(0xFFDD2222).withOpacity(0.4 * v),
                      Colors.transparent,
                    ]),
                  ),
                );
              },
            ),
          ),

          // === SEARCHLIGHT ===
          Positioned(
            top: 0,
            right: size.width * 0.22,
            child: AnimatedBuilder(
              animation: _waveController,
              builder: (_, __) {
                final angle = sin(_waveController.value * 2 * pi) * 0.10;
                return Transform.rotate(
                  angle: angle,
                  alignment: Alignment.topCenter,
                  child: Container(
                    width: 70,
                    height: size.height * 0.52,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.white.withOpacity(0.10),
                          Colors.white.withOpacity(0.0),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // === TITLE + BUTTON ===
          SafeArea(
            child: Column(
              children: [
                const Spacer(flex: 2),

                ScaleTransition(
                  scale: _titleAnim,
                  child: Column(
                    children: [
                      // Eyebrow label
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _divider(),
                          const SizedBox(width: 14),
                          const Text(
                            'NAVAL COMMAND',
                            style: TextStyle(
                              color: Color(0xFF00E5FF), // vivid cyan — projects well on wood
                              fontSize: 12,
                              letterSpacing: 7,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(width: 14),
                          _divider(),
                        ],
                      ),
                      const SizedBox(height: 12),

                      // Main title — stark white with cyan glow
                      Stack(
                        alignment: Alignment.center,
                        children: [
                          // Glow layer
                          const Text(
                            'BATTLE\nSHIPS',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 80,
                              fontWeight: FontWeight.w900,
                              color: Color(0xFF00E5FF),
                              height: 0.88,
                              letterSpacing: 10,
                              shadows: [
                                Shadow(color: Color(0xCC00E5FF), blurRadius: 40),
                                Shadow(color: Color(0x8800E5FF), blurRadius: 80),
                              ],
                            ),
                          ),
                          // Sharp white text on top
                          const Text(
                            'BATTLE\nSHIPS',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 80,
                              fontWeight: FontWeight.w900,
                              color: Colors.white,
                              height: 0.88,
                              letterSpacing: 10,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 16),
                      const Text(
                        '— SINK OR BE SUNK —',
                        style: TextStyle(
                          color: Color(0xFFFF6F00),
                          fontSize: 13,
                          letterSpacing: 5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),

                const Spacer(flex: 3),

                // Big tap target — 72px tall, glowing border, easy to hit on projector
                ScaleTransition(
                  scale: _pulseAnim,
                  child: GestureDetector(
                    onTap: widget.onPlay,
                    child: Container(
                      width: 260,
                      height: 72,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(4),
                        color: Colors.black,
                        border: Border.all(color: const Color(0xFF00E5FF), width: 2.5),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.5),
                            blurRadius: 24,
                            spreadRadius: 3,
                          ),
                          BoxShadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.2),
                            blurRadius: 50,
                            spreadRadius: 8,
                          ),
                        ],
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.play_arrow_rounded, color: Color(0xFF00E5FF), size: 32),
                          SizedBox(width: 10),
                          Text(
                            'DEPLOY FLEET',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 18),
                const Text(
                  '2 PLAYERS  •  11 SHIPS  •  1 WINNER',
                  style: TextStyle(
                    color: Colors.white30,
                    fontSize: 12,
                    letterSpacing: 3,
                    fontWeight: FontWeight.w600,
                  ),
                ),

                const Spacer(flex: 2),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _divider() => Container(
    width: 44, height: 1.5,
    color: const Color(0xFF00E5FF).withOpacity(0.5),
  );
}

// ─── Ocean Wave Painter ───────────────────────────────────────────────────────
// Waves use teal/cyan tones — these contrast well against dark wood grain

class _OceanPainter extends CustomPainter {
  final double t;
  _OceanPainter(this.t);

  @override
  void paint(Canvas canvas, Size size) {
    final h = size.height;
    final w = size.width;
    _wave(canvas, w, h, t, 0.71, const Color(0xFF00303F), amp: 20, freq: 1.2);
    _wave(canvas, w, h, t, 0.73, const Color(0xFF004050), amp: 15, freq: 1.7, off: 0.3);
    _wave(canvas, w, h, t, 0.75, const Color(0xFF003545), amp: 11, freq: 2.0, off: 0.7);
    _wave(canvas, w, h, t, 0.77, const Color(0xFF002535), amp: 8,  freq: 1.4, off: 1.2);
  }

  void _wave(Canvas canvas, double w, double h, double t, double yFrac, Color color,
      {double amp = 12, double freq = 1, double off = 0}) {
    final paint = Paint()..color = color;
    final path = Path();
    final baseY = h * yFrac;
    path.moveTo(0, baseY);
    for (double x = 0; x <= w; x += 2) {
      path.lineTo(x, baseY + amp * sin((x / w * 2 * pi * freq) + t * 2 * pi + off));
    }
    path.lineTo(w, h);
    path.lineTo(0, h);
    path.close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_OceanPainter old) => old.t != t;
}

// ─── Ship Silhouette Painter ──────────────────────────────────────────────────
// Ship uses a slightly lighter charcoal than pure black so it reads as a silhouette

class _ShipSilhouettePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()..color = const Color(0xFF111C26)..style = PaintingStyle.fill;
    final w = size.width;
    final h = size.height;

    // Hull
    canvas.drawPath(
      Path()
        ..moveTo(w * 0.05, h * 0.72)
        ..lineTo(w * 0.08, h * 0.54)
        ..lineTo(w * 0.88, h * 0.54)
        ..lineTo(w * 0.95, h * 0.72)
        ..lineTo(w * 0.92, h * 0.82)
        ..lineTo(w * 0.08, h * 0.82)
        ..close(),
      p,
    );

    // Superstructure
    canvas.drawPath(
      Path()
        ..moveTo(w * 0.35, h * 0.54)
        ..lineTo(w * 0.38, h * 0.28)
        ..lineTo(w * 0.65, h * 0.28)
        ..lineTo(w * 0.68, h * 0.54)
        ..close(),
      p,
    );

    // Tower
    canvas.drawPath(
      Path()
        ..moveTo(w * 0.46, h * 0.28)
        ..lineTo(w * 0.48, h * 0.08)
        ..lineTo(w * 0.54, h * 0.08)
        ..lineTo(w * 0.56, h * 0.28)
        ..close(),
      p,
    );

    // Gun barrels — slightly visible stroke
    final gun = Paint()
      ..color = const Color(0xFF0D1821)
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke;
    canvas.drawLine(Offset(w * 0.30, h * 0.44), Offset(w * 0.14, h * 0.38), gun);
    canvas.drawLine(Offset(w * 0.72, h * 0.44), Offset(w * 0.86, h * 0.38), gun);

    // Water reflection
    canvas.drawPath(
      Path()
        ..moveTo(w * 0.08, h * 0.82)
        ..lineTo(w * 0.92, h * 0.82)
        ..lineTo(w * 0.88, h * 0.97)
        ..lineTo(w * 0.12, h * 0.97)
        ..close(),
      Paint()..color = const Color(0xFF001520).withOpacity(0.6),
    );
  }

  @override
  bool shouldRepaint(_ShipSilhouettePainter _) => false;
}