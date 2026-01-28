import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A custom transition page that provides smooth fade transitions
/// between bottom navigation tabs.
/// 
/// This page uses a [FadeTransition] with a 200ms duration and 
/// [Curves.easeInOut] curve to create a smooth visual transition.
class FadeTransitionPage<T> extends CustomTransitionPage<T> {
  FadeTransitionPage({
    required super.child,
    super.key,
  }) : super(
          transitionDuration: const Duration(milliseconds: 200),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeInOut,
              ),
              child: child,
            );
          },
        );
}

