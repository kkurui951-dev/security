import 'package:flutter/material.dart';
import 'package:university_secure_chat/features/auth/login_view.dart';
import 'package:university_secure_chat/features/navigation/main_navigation_scaffold.dart';
import 'package:university_secure_chat/services/api_service.dart';
import 'package:university_secure_chat/services/notification_service.dart';
import 'package:university_secure_chat/services/session_service.dart';

void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize local notifications service
  await NotificationService.initialize();

  // Check if a guard session is saved locally on the device
  String? savedBadge = await SessionService.getSavedUserSession();
  Map<String, dynamic>? cachedUser;

  if (savedBadge != null) {
    try {
      // Fetch guards list from Python FastAPI backend on Render
      final guards = await ApiService.fetchGuards();
      cachedUser = guards.firstWhere(
        (g) => g['badgeNumber'] == savedBadge,
        orElse: () => null,
      );
    } catch (e) {
      cachedUser = null;
    }
  }

  runApp(MyApp(initialUser: cachedUser));
}

class MyApp extends StatelessWidget {
  final Map<String, dynamic>? initialUser;
  const MyApp({super.key, this.initialUser});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'University Security Guard Chat',
      theme: ThemeData(
        primarySwatch: Colors.green,
        scaffoldBackgroundColor: const Color(0xFF063826),
      ),
      // If a valid cached user session exists, skip login and launch main scaffold
      home: initialUser != null
          ? MainNavigationScaffold(currentUser: initialUser!)
          : const LoginView(),
    );
  }
}
