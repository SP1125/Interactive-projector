import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/game_screen.dart';

void main() {
  runApp(const BattleshipsApp());
}

class BattleshipsApp extends StatelessWidget {
  const BattleshipsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Battleships',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF080E18),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF42A5F5),
          surface: Color(0xFF0D1B2A),
        ),
        dialogBackgroundColor: const Color(0xFF0D1B2A),
        snackBarTheme: const SnackBarThemeData(
          behavior: SnackBarBehavior.floating,
        ),
      ),
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell>
    with SingleTickerProviderStateMixin {
  bool _showGame = false;
  late AnimationController _slideController;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, -1), // home slides up off screen
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeInOutCubic,
    ));
  }

  @override
  void dispose() {
    _slideController.dispose();
    super.dispose();
  }

  void _onPlay() {
    setState(() => _showGame = true);
    _slideController.forward();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Home screen — always underneath
        if (!_showGame || _slideController.value < 1)
          HomeScreen(onPlay: _onPlay),

        // Game screen — slides in from below
        if (_showGame)
          SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 1), // starts below screen
              end: Offset.zero,          // slides up into view
            ).animate(CurvedAnimation(
              parent: _slideController,
              curve: Curves.easeInOutCubic,
            )),
            child: const GameScreen(),
          ),
      ],
    );
  }
}