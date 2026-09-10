import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class QRScreen extends StatefulWidget {
  const QRScreen({super.key});

  @override
  State<QRScreen> createState() => _QRScreenState();
}

class _QRScreenState extends State<QRScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnim;

  // Simulated tickets
  final List<QRTicket> _tickets = [
    QRTicket(
      id: 'PP${Random().nextInt(99999).toString().padLeft(5, '0')}',
      lotName: 'ParkPilot Central',
      slotNumber: 'A-01',
      entryTime: DateTime.now().subtract(const Duration(hours: 1)),
      expiryTime: DateTime.now().add(const Duration(hours: 2)),
      type: 'Active',
      status: TicketStatus.active,
    ),
    QRTicket(
      id: 'PP77231',
      lotName: 'ParkPilot North',
      slotNumber: 'B-07',
      entryTime: DateTime.now().subtract(const Duration(days: 1, hours: 3)),
      expiryTime:
          DateTime.now().subtract(const Duration(days: 1)),
      type: 'Past',
      status: TicketStatus.expired,
    ),
  ];

  int _selectedTicket = 0;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
        vsync: this, duration: const Duration(seconds: 2))
      ..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 1.0, end: 1.08).animate(
        CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ticket = _tickets[_selectedTicket];

    return Scaffold(
      appBar: AppBar(
        title: const Text('My QR Tickets'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              HapticFeedback.lightImpact();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Tickets refreshed')),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Ticket selector
          if (_tickets.length > 1) ...[
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: List.generate(
                  _tickets.length,
                  (i) => Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _selectedTicket = i),
                      child: Container(
                        margin: const EdgeInsets.only(right: i < _tickets.length - 1 ? 8 : 0),
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: _selectedTicket == i
                              ? const Color(0xFF2563EB)
                              : const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                              color: _selectedTicket == i
                                  ? const Color(0xFF2563EB)
                                  : const Color(0xFF334155)),
                        ),
                        child: Text(
                          _tickets[i].type,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                              color: _selectedTicket == i
                                  ? Colors.white
                                  : const Color(0xFF64748B),
                              fontWeight: FontWeight.w600,
                              fontSize: 13),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                children: [
                  // Main QR Card
                  _buildQRCard(ticket),
                  const SizedBox(height: 20),
                  // Details
                  _buildDetailsCard(ticket),
                  const SizedBox(height: 20),
                  // Actions
                  if (ticket.status == TicketStatus.active)
                    _buildActionsCard(ticket),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQRCard(QRTicket ticket) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: ticket.status == TicketStatus.active
              ? const Color(0xFF2563EB).withOpacity(0.5)
              : const Color(0xFF334155),
          width: 1.5,
        ),
      ),
      child: Column(
        children: [
          // Status Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: ticket.statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: ticket.statusColor.withOpacity(0.4)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: ticket.statusColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  ticket.statusLabel,
                  style: TextStyle(
                      color: ticket.statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 13),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // QR Code Visual
          AnimatedBuilder(
            animation: _pulseAnim,
            builder: (_, child) => Transform.scale(
              scale: ticket.status == TicketStatus.active
                  ? _pulseAnim.value
                  : 1.0,
              child: child,
            ),
            child: Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: ticket.status == TicketStatus.active
                    ? [
                        BoxShadow(
                          color: const Color(0xFF2563EB).withOpacity(0.3),
                          blurRadius: 30,
                          spreadRadius: 5,
                        )
                      ]
                    : null,
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // QR pattern simulation
                  CustomPaint(
                    size: const Size(160, 160),
                    painter: _QRPatternPainter(
                        seed: ticket.id.hashCode,
                        active: ticket.status == TicketStatus.active),
                  ),
                  if (ticket.status == TicketStatus.expired)
                    Container(
                      color: Colors.black54,
                      child: const Center(
                        child: Text('EXPIRED',
                            style: TextStyle(
                                color: Colors.red,
                                fontWeight: FontWeight.bold,
                                fontSize: 20)),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            ticket.id,
            style: const TextStyle(
              color: Color(0xFF94A3B8),
              fontSize: 14,
              letterSpacing: 3,
              fontFamily: 'monospace',
            ),
          ),
          const SizedBox(height: 8),
          Text(
            ticket.lotName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            'Slot ${ticket.slotNumber}',
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsCard(QRTicket ticket) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Ticket Details',
              style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16)),
          const SizedBox(height: 16),
          _buildDetailRow(
              Icons.login_rounded, 'Entry',
              _formatTime(ticket.entryTime)),
          _buildDetailRow(
              Icons.logout_rounded, 'Exit',
              _formatTime(ticket.expiryTime)),
          _buildDetailRow(
              Icons.timer_outlined, 'Duration',
              _formatDuration(ticket.expiryTime.difference(ticket.entryTime))),
          _buildDetailRow(Icons.location_on_outlined, 'Location', ticket.lotName),
        ],
      ),
    );
  }

  Widget _buildActionsCard(QRTicket ticket) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildActionButton(
                icon: Icons.share_rounded,
                label: 'Share',
                color: const Color(0xFF7C3AED),
                onTap: () => HapticFeedback.lightImpact(),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActionButton(
                icon: Icons.download_rounded,
                label: 'Save',
                color: const Color(0xFF0891B2),
                onTap: () => HapticFeedback.lightImpact(),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActionButton(
                icon: Icons.cancel_outlined,
                label: 'Cancel',
                color: const Color(0xFFEF4444),
                onTap: () => _showCancelDialog(ticket),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDetailRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF64748B)),
          const SizedBox(width: 12),
          Text(label,
              style: const TextStyle(
                  color: Color(0xFF64748B), fontSize: 14, width: 64)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(value,
                style: const TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 14,
                    fontWeight: FontWeight.w500),
                textAlign: TextAlign.end),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(height: 4),
            Text(label,
                style: TextStyle(
                    color: color, fontSize: 12, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  void _showCancelDialog(QRTicket ticket) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Cancel Booking',
            style: TextStyle(color: Colors.white)),
        content: const Text(
            'Are you sure you want to cancel this booking? Refunds will be processed within 24 hours.',
            style: TextStyle(color: Color(0xFF94A3B8))),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Keep Booking',
                  style: TextStyle(color: Color(0xFF64748B)))),
          TextButton(
              onPressed: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                      content: Text('Booking cancelled. Refund initiated.')),
                );
              },
              child: const Text('Cancel',
                  style: TextStyle(color: Color(0xFFEF4444)))),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) =>
      '${dt.day}/${dt.month} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';

  String _formatDuration(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes % 60;
    return '${h}h ${m}m';
  }
}

enum TicketStatus { active, expired, used }

class QRTicket {
  final String id;
  final String lotName;
  final String slotNumber;
  final DateTime entryTime;
  final DateTime expiryTime;
  final String type;
  final TicketStatus status;

  const QRTicket({
    required this.id,
    required this.lotName,
    required this.slotNumber,
    required this.entryTime,
    required this.expiryTime,
    required this.type,
    required this.status,
  });

  Color get statusColor {
    switch (status) {
      case TicketStatus.active:
        return const Color(0xFF10B981);
      case TicketStatus.expired:
        return const Color(0xFF64748B);
      case TicketStatus.used:
        return const Color(0xFF2563EB);
    }
  }

  String get statusLabel {
    switch (status) {
      case TicketStatus.active:
        return 'Active';
      case TicketStatus.expired:
        return 'Expired';
      case TicketStatus.used:
        return 'Used';
    }
  }
}

// QR pattern painter
class _QRPatternPainter extends CustomPainter {
  final int seed;
  final bool active;
  _QRPatternPainter({required this.seed, required this.active});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = active ? const Color(0xFF0F172A) : Colors.grey.shade600
      ..style = PaintingStyle.fill;
    final rng = Random(seed);
    const cell = 8.0;
    final cols = (size.width / cell).floor();
    final rows = (size.height / cell).floor();
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        if (rng.nextBool()) {
          canvas.drawRect(
            Rect.fromLTWH(c * cell, r * cell, cell - 1, cell - 1),
            paint,
          );
        }
      }
    }
    // Corner squares
    final cornerPaint = Paint()
      ..color = active ? const Color(0xFF0F172A) : Colors.grey.shade600;
    for (final (cx, cy) in [(0.0, 0.0), (size.width - 28, 0.0), (0.0, size.height - 28)]) {
      canvas.drawRect(Rect.fromLTWH(cx, cy, 28, 28), cornerPaint);
      canvas.drawRect(
          Rect.fromLTWH(cx + 4, cy + 4, 20, 20), Paint()..color = Colors.white);
      canvas.drawRect(Rect.fromLTWH(cx + 8, cy + 8, 12, 12), cornerPaint);
    }
  }

  @override
  bool shouldRepaint(_QRPatternPainter old) =>
      old.seed != seed || old.active != active;
}
