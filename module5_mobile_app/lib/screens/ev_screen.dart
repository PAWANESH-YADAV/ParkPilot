import 'package:flutter/material.dart';

class EVScreen extends StatefulWidget {
  const EVScreen({super.key});

  @override
  State<EVScreen> createState() => _EVScreenState();
}

class _EVScreenState extends State<EVScreen> {
  final List<EVCharger> _chargers = [
    EVCharger(
      id: 'EV-01',
      location: 'ParkPilot Central — Level 1',
      type: 'CCS2 (50 kW)',
      status: ChargerStatus.available,
      pricePerKwh: 12.0,
      queueCount: 0,
    ),
    EVCharger(
      id: 'EV-02',
      location: 'ParkPilot Central — Level 1',
      type: 'Type 2 (22 kW)',
      status: ChargerStatus.occupied,
      pricePerKwh: 8.0,
      currentUser: 'MH12AB3456',
      kwhSoFar: 18.5,
      sessionMinutes: 45,
      queueCount: 2,
    ),
    EVCharger(
      id: 'EV-03',
      location: 'ParkPilot Central — Level 2',
      type: 'CCS2 (50 kW)',
      status: ChargerStatus.available,
      pricePerKwh: 12.0,
      queueCount: 0,
    ),
    EVCharger(
      id: 'EV-04',
      location: 'ParkPilot North — G1',
      type: 'Type 1 (7.4 kW)',
      status: ChargerStatus.fault,
      pricePerKwh: 6.0,
      queueCount: 0,
    ),
  ];

  EVCharger? _selectedForSession;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('EV Charging'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline_rounded),
            onPressed: _showRatesInfo,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSummaryHeader(),
            const SizedBox(height: 24),
            const Text('Charging Stations',
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            ..._chargers.map((c) => _buildChargerCard(c)),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryHeader() {
    final available = _chargers.where((c) => c.status == ChargerStatus.available).length;
    final occupied = _chargers.where((c) => c.status == ChargerStatus.occupied).length;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF065F46), Color(0xFF0F766E)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.bolt_rounded, color: Color(0xFF34D399), size: 28),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('EV Charging Network',
                        style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16)),
                    Text('Smart charging with dynamic pricing',
                        style: TextStyle(
                            color: Color(0xFF6EE7B7), fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              _buildMiniStat('$available', 'Available', const Color(0xFF34D399)),
              _buildMiniStat('$occupied', 'Occupied', const Color(0xFFF59E0B)),
              _buildMiniStat(
                  '${_chargers.length}', 'Total', const Color(0xFF60A5FA)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMiniStat(String value, String label, Color color) {
    return Expanded(
      child: Column(
        children: [
          Text(value,
              style: TextStyle(
                  color: color, fontSize: 24, fontWeight: FontWeight.bold)),
          Text(label,
              style:
                  const TextStyle(color: Color(0xFF6EE7B7), fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildChargerCard(EVCharger charger) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: charger.statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                        color: charger.statusColor.withOpacity(0.4)),
                  ),
                  child: Icon(
                    charger.status == ChargerStatus.fault
                        ? Icons.warning_amber_rounded
                        : Icons.ev_station_rounded,
                    color: charger.statusColor,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(charger.id,
                          style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16)),
                      Text(charger.location,
                          style: const TextStyle(
                              color: Color(0xFF64748B), fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: charger.statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(charger.statusLabel,
                      style: TextStyle(
                          color: charger.statusColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 12)),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildInfoChip(Icons.electrical_services_rounded, charger.type),
                const SizedBox(width: 8),
                _buildInfoChip(Icons.currency_rupee_rounded,
                    '₹${charger.pricePerKwh}/kWh'),
              ],
            ),
            if (charger.status == ChargerStatus.occupied) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF59E0B).withOpacity(0.05),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                      color: const Color(0xFFF59E0B).withOpacity(0.2)),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Current Session',
                            style: TextStyle(
                                color: Color(0xFF94A3B8), fontSize: 12)),
                        Text('${charger.sessionMinutes} min',
                            style: const TextStyle(
                                color: Color(0xFFF59E0B), fontSize: 12)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('${charger.kwhSoFar} kWh charged',
                            style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600)),
                        Text(
                            '₹${(charger.kwhSoFar * charger.pricePerKwh).toStringAsFixed(0)}',
                            style: const TextStyle(
                                color: Color(0xFFF59E0B),
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                    if (charger.queueCount > 0) ...[
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          const Icon(Icons.people_alt_outlined,
                              size: 14, color: Color(0xFF64748B)),
                          const SizedBox(width: 4),
                          Text('${charger.queueCount} vehicle(s) waiting',
                              style: const TextStyle(
                                  color: Color(0xFF64748B), fontSize: 12)),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
            const SizedBox(height: 12),
            if (charger.status == ChargerStatus.available)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _startSession(charger),
                  icon: const Icon(Icons.bolt_rounded, size: 18),
                  label: const Text('Start Charging'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              )
            else if (charger.status == ChargerStatus.occupied &&
                charger.queueCount >= 0)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => _joinQueue(charger),
                  icon: const Icon(Icons.queue_rounded, size: 18),
                  label: Text(
                      'Join Queue (${charger.queueCount + 1} position)'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFF59E0B),
                    side: const BorderSide(color: Color(0xFFF59E0B)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: const Color(0xFF64748B)),
          const SizedBox(width: 5),
          Text(text,
              style: const TextStyle(
                  color: Color(0xFF94A3B8), fontSize: 12)),
        ],
      ),
    );
  }

  void _startSession(EVCharger charger) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Start Charging Session',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 20)),
            const SizedBox(height: 8),
            Text('Charger: ${charger.id} — ${charger.type}',
                style: const TextStyle(color: Color(0xFF94A3B8))),
            Text('Rate: ₹${charger.pricePerKwh}/kWh',
                style: const TextStyle(color: Color(0xFF10B981))),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                      content: Text(
                          'Charging started on ${charger.id}. You\'ll be notified when complete.')),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF10B981),
                minimumSize: const Size(double.infinity, 52),
              ),
              child: const Text('Confirm & Start'),
            ),
          ],
        ),
      ),
    );
  }

  void _joinQueue(EVCharger charger) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
          content: Text(
              'Added to queue for ${charger.id}. You\'ll be notified when available.')),
    );
  }

  void _showRatesInfo() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Charging Rates',
            style: TextStyle(color: Colors.white)),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _RateRow('CCS2 (50 kW)', '₹12/kWh'),
            _RateRow('Type 2 (22 kW)', '₹8/kWh'),
            _RateRow('Type 1 (7.4 kW)', '₹6/kWh'),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'))
        ],
      ),
    );
  }
}

class _RateRow extends StatelessWidget {
  final String type;
  final String rate;
  const _RateRow(this.type, this.rate);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(type,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 14)),
          Text(rate,
              style: const TextStyle(
                  color: Color(0xFF10B981),
                  fontWeight: FontWeight.bold,
                  fontSize: 14)),
        ],
      ),
    );
  }
}

enum ChargerStatus { available, occupied, fault }

class EVCharger {
  final String id;
  final String location;
  final String type;
  final ChargerStatus status;
  final double pricePerKwh;
  final String? currentUser;
  final double kwhSoFar;
  final int sessionMinutes;
  final int queueCount;

  const EVCharger({
    required this.id,
    required this.location,
    required this.type,
    required this.status,
    required this.pricePerKwh,
    this.currentUser,
    this.kwhSoFar = 0,
    this.sessionMinutes = 0,
    this.queueCount = 0,
  });

  Color get statusColor {
    switch (status) {
      case ChargerStatus.available:
        return const Color(0xFF10B981);
      case ChargerStatus.occupied:
        return const Color(0xFFF59E0B);
      case ChargerStatus.fault:
        return const Color(0xFFEF4444);
    }
  }

  String get statusLabel {
    switch (status) {
      case ChargerStatus.available:
        return 'Available';
      case ChargerStatus.occupied:
        return 'Occupied';
      case ChargerStatus.fault:
        return 'Fault';
    }
  }
}
