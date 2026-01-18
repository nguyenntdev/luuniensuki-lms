import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/network_info.dart';
import '../../core/theme/app_colors.dart';

class NetworkStatusIndicator extends ConsumerStatefulWidget {
  final Widget child;

  const NetworkStatusIndicator({
    super.key,
    required this.child,
  });

  @override
  ConsumerState<NetworkStatusIndicator> createState() =>
      _NetworkStatusIndicatorState();
}

class _NetworkStatusIndicatorState extends ConsumerState<NetworkStatusIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<Offset> _slideAnimation;
  bool _wasOffline = false;
  bool _showBanner = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, -1),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));

    _checkInitialConnection();
  }

  Future<void> _checkInitialConnection() async {
    final networkInfo = ref.read(networkInfoProvider);
    final isConnected = await networkInfo.isConnected;
    if (!isConnected) {
      setState(() {
        _wasOffline = true;
        _showBanner = true;
      });
      _animationController.forward();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _handleConnectionChange(bool isConnected) {
    if (!isConnected && !_showBanner) {
      setState(() {
        _wasOffline = true;
        _showBanner = true;
      });
      _animationController.forward();
    } else if (isConnected && _wasOffline && _showBanner) {
      _animationController.reverse().then((_) {
        if (mounted) {
          setState(() {
            _showBanner = false;
            _wasOffline = false;
          });
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<bool>>(connectivityStatusProvider, (previous, next) {
      next.whenData((isConnected) {
        _handleConnectionChange(isConnected);
      });
    });

    return Stack(
      children: [
        widget.child,
        if (_showBanner)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SlideTransition(
              position: _slideAnimation,
              child: Material(
                elevation: 4,
                child: Container(
                  padding: EdgeInsets.only(
                    top: MediaQuery.of(context).padding.top + 8,
                    bottom: 8,
                    left: 16,
                    right: 16,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.error,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.black.withOpacity(0.2),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.wifi_off_rounded,
                        color: AppColors.white,
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Không có kết nối mạng',
                          style: TextStyle(
                            color: AppColors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
