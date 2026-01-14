import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/storage/hive_storage.dart';
import '../../domain/entities/gem_transaction.dart';

part 'gems_provider.g.dart';

const int _initialGems = 100; // Starting gems for new users
const String _gemsKey = 'gems_balance';
const String _transactionsKey = 'gems_transactions';

/// Simple UUID generator
String _generateId() {
  final now = DateTime.now().millisecondsSinceEpoch;
  final random = (now % 1000000).toString();
  return 'gem_$now$random';
}

/// Gems state
class GemsState {
  final int balance;
  final List<GemTransaction> transactions;
  final bool isLoading;
  final String? error;

  const GemsState({
    required this.balance,
    required this.transactions,
    this.isLoading = false,
    this.error,
  });

  GemsState copyWith({
    int? balance,
    List<GemTransaction>? transactions,
    bool? isLoading,
    String? error,
  }) {
    return GemsState(
      balance: balance ?? this.balance,
      transactions: transactions ?? this.transactions,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Gems notifier
@Riverpod(keepAlive: true)
class GemsNotifier extends _$GemsNotifier {
  @override
  GemsState build() {
    _loadFromStorage();
    return const GemsState(
      balance: _initialGems,
      transactions: [],
    );
  }

  HiveStorage get _storage => ref.read(hiveStorageProvider);

  /// Load gems data from local storage
  void _loadFromStorage() {
    final balance = _storage.getSetting<int>(_gemsKey, defaultValue: _initialGems);
    final transactionsData = _storage.getSetting<List>(_transactionsKey, defaultValue: []);

    final transactions = transactionsData!
        .map((json) => _transactionFromJson(json as Map<String, dynamic>))
        .toList();

    state = GemsState(
      balance: balance!,
      transactions: transactions,
    );
  }

  /// Save to storage
  Future<void> _saveToStorage() async {
    await _storage.setSetting(_gemsKey, state.balance);
    await _storage.setSetting(
      _transactionsKey,
      state.transactions.map((t) => _transactionToJson(t)).toList(),
    );
  }

  /// Add gems
  Future<bool> addGems({
    required int amount,
    required GemTransactionType type,
    String? description,
  }) async {
    if (amount <= 0) return false;

    final transaction = GemTransaction(
      id: _generateId(),
      amount: amount,
      type: type,
      description: description ?? type.displayName,
      createdAt: DateTime.now(),
    );

    state = state.copyWith(
      balance: state.balance + amount,
      transactions: [transaction, ...state.transactions],
    );

    await _saveToStorage();
    return true;
  }

  /// Spend gems
  Future<bool> spendGems({
    required int amount,
    required GemTransactionType type,
    String? description,
  }) async {
    if (amount <= 0 || state.balance < amount) return false;

    final transaction = GemTransaction(
      id: _generateId(),
      amount: -amount,
      type: type,
      description: description ?? type.displayName,
      createdAt: DateTime.now(),
    );

    state = state.copyWith(
      balance: state.balance - amount,
      transactions: [transaction, ...state.transactions],
    );

    await _saveToStorage();
    return true;
  }

  /// Get balance
  int getBalance() => state.balance;

  /// Get transaction history
  List<GemTransaction> getTransactionHistory() => state.transactions;

  /// Check if user can afford
  bool canAfford(int amount) => state.balance >= amount;

  /// Convert transaction to JSON
  Map<String, dynamic> _transactionToJson(GemTransaction transaction) {
    return {
      'id': transaction.id,
      'amount': transaction.amount,
      'type': transaction.type.value,
      'description': transaction.description,
      'created_at': transaction.createdAt.toIso8601String(),
    };
  }

  /// Convert JSON to transaction
  GemTransaction _transactionFromJson(Map<String, dynamic> json) {
    return GemTransaction(
      id: json['id'] as String,
      amount: json['amount'] as int,
      type: GemTransactionType.fromValue(json['type'] as String),
      description: json['description'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

