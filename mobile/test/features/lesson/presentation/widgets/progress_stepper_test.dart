import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:luuniensuki_lms/features/lesson/presentation/widgets/progress_stepper.dart';

void main() {
  group('ProgressStepper', () {
    testWidgets('shows correct state for hidden status', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'hidden'),
          ),
        ),
      );

      expect(find.text('1'), findsOneWidget);
      expect(find.byIcon(Icons.lock), findsNWidgets(2));
      expect(find.byIcon(Icons.check), findsNothing);
      
      expect(find.text('Khám Phá'), findsOneWidget);
      expect(find.text('Bài Học'), findsOneWidget);
      expect(find.text('Trắc Nghiệm'), findsOneWidget);
      
      expect(find.text('+25 XP'), findsOneWidget);
      expect(find.text('+50 XP'), findsOneWidget);
      expect(find.text('+75 XP'), findsOneWidget);
    });

    testWidgets('shows correct state for discovered status', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'discovered'),
          ),
        ),
      );

      expect(find.byIcon(Icons.check), findsOneWidget);
      expect(find.text('2'), findsOneWidget);
      expect(find.byIcon(Icons.lock), findsOneWidget);
      
      expect(find.text('Khám Phá'), findsOneWidget);
      expect(find.text('Bài Học'), findsOneWidget);
      expect(find.text('Trắc Nghiệm'), findsOneWidget);
      
      expect(find.text('+25 XP'), findsOneWidget);
      expect(find.text('+50 XP'), findsOneWidget);
      expect(find.text('+75 XP'), findsOneWidget);
    });

    testWidgets('shows correct state for learned status', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'learned'),
          ),
        ),
      );

      expect(find.byIcon(Icons.check), findsNWidgets(2));
      expect(find.text('3'), findsOneWidget);
      expect(find.byIcon(Icons.lock), findsNothing);
      
      expect(find.text('Khám Phá'), findsOneWidget);
      expect(find.text('Bài Học'), findsOneWidget);
      expect(find.text('Trắc Nghiệm'), findsOneWidget);
      
      expect(find.text('+25 XP'), findsOneWidget);
      expect(find.text('+50 XP'), findsOneWidget);
      expect(find.text('+75 XP'), findsOneWidget);
    });

    testWidgets('shows correct state for mastered status', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'mastered'),
          ),
        ),
      );

      expect(find.byIcon(Icons.check), findsNWidgets(3));
      expect(find.byIcon(Icons.lock), findsNothing);
      
      expect(find.text('Khám Phá'), findsOneWidget);
      expect(find.text('Bài Học'), findsOneWidget);
      expect(find.text('Trắc Nghiệm'), findsOneWidget);
      
      expect(find.text('+25 XP'), findsOneWidget);
      expect(find.text('+50 XP'), findsOneWidget);
      expect(find.text('+75 XP'), findsOneWidget);
    });

    testWidgets('XP values are displayed correctly for all statuses', (tester) async {
      const statuses = ['hidden', 'discovered', 'learned', 'mastered'];
      
      for (final status in statuses) {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: ProgressStepper(status: status),
            ),
          ),
        );
        
        expect(find.text('+25 XP'), findsOneWidget, reason: 'XP 25 not found for status: $status');
        expect(find.text('+50 XP'), findsOneWidget, reason: 'XP 50 not found for status: $status');
        expect(find.text('+75 XP'), findsOneWidget, reason: 'XP 75 not found for status: $status');
        
        expect(find.byIcon(Icons.star), findsNWidgets(3), reason: 'Star icons not found for status: $status');
      }
    });

    testWidgets('handles case-insensitive status values', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'DISCOVERED'),
          ),
        ),
      );

      expect(find.byIcon(Icons.check), findsOneWidget);
      expect(find.text('2'), findsOneWidget);
    });

    testWidgets('handles unknown status as hidden', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProgressStepper(status: 'unknown_status'),
          ),
        ),
      );

      expect(find.text('1'), findsOneWidget);
      expect(find.byIcon(Icons.lock), findsNWidgets(2));
      expect(find.byIcon(Icons.check), findsNothing);
    });
  });
}

