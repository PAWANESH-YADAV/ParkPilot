import 'package:flutter/material.dart';
import 'home_screen.dart';

class BookingScreen extends StatefulWidget {
  final ParkingLot? lot;
  const BookingScreen({super.key, this.lot});

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  DateTime _startTime = DateTime.now();
  DateTime _endTime = DateTime.now().add(const Duration(hours: 2));
  String _selectedSlot = 'A-01';
  String _vehicleType = 'car';
  bool _isBooking = false;
  bool _isBooked = false;

  final List<String> _slots = ['A-01', 'A-02', 'A-05', 'B-03', 'B-07', 'C-12'];
  final List<Map<String, dynamic>> _vehicleTypes = [
    {'type': 'car', 'icon': Icons.directions_car_rounded, 'label': 'Car'},
    {'type': 'bike', 'icon': Icons.two_wheeler_rounded, 'label': 'Bike'},
    {'type': 'ev', 'icon': Icons.electric_car_rounded, 'label': 'EV'},
    {'type': 'truck', 'icon': Icons.local_shipping_rounded, 'label': 'Truck'},
  ];

  double get _durationHours =>
      _endTime.difference(_startTime).inMinutes / 60.0;

  double get _totalAmount {
    final base = (widget.lot?.pricePerHour ?? 30.0) * _durationHours;
    if (_vehicleType == 'ev') return base * 0.9; // 10% EV discount
    if (_vehicleType == 'bike') return base * 0.5;
    return base;
  }

  Future<void> _pickTime(bool isStart) async {
    final now = DateTime.now();
    final initial = isStart ? _startTime : _endTime;
    final picked = await showDateTimePicker(context, initial, now);
    if (picked != null) {
      setState(() {
        if (isStart) {
          _startTime = picked;
          if (_endTime.isBefore(_startTime.add(const Duration(hours: 1)))) {
            _endTime = _startTime.add(const Duration(hours: 1));
          }
        } else {
          _endTime = picked;
        }
      });
    }
  }

  Future<DateTime?> showDateTimePicker(
      BuildContext context, DateTime initial, DateTime first) async {
    final date = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: first,
      lastDate: first.add(const Duration(days: 30)),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.dark(primary: Color(0xFF2563EB)),
        ),
        child: child!,
      ),
    );
    if (date == null) return null;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.dark(primary: Color(0xFF2563EB)),
        ),
        child: child!,
      ),
    );
    if (time == null) return null;
    return DateTime(date.year, date.month, date.day, time.hour, time.minute);
  }

  Future<void> _confirmBooking() async {
    setState(() => _isBooking = true);
    await Future.delayed(const Duration(seconds: 2)); // Simulated API call
    setState(() {
      _isBooking = false;
      _isBooked = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isBooked) return _buildSuccessScreen();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Book a Slot'),
        leading: const BackButton(),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Lot Info
            if (widget.lot != null) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1E3A8A), Color(0xFF1E40AF)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.local_parking_rounded,
                          color: Colors.white, size: 28),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(widget.lot!.name,
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16)),
                          Text(widget.lot!.address,
                              style: const TextStyle(
                                  color: Color(0xFFBFDBFE), fontSize: 13)),
                          Text('${widget.lot!.available} slots available',
                              style: const TextStyle(
                                  color: Color(0xFF34D399), fontSize: 13)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],
            // Vehicle Type
            const Text('Vehicle Type',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16)),
            const SizedBox(height: 12),
            Row(
              children: _vehicleTypes.map((v) {
                final isSelected = _vehicleType == v['type'];
                return Expanded(
                  child: GestureDetector(
                    onTap: () => setState(() => _vehicleType = v['type']),
                    child: Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? const Color(0xFF2563EB)
                            : const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isSelected
                              ? const Color(0xFF2563EB)
                              : const Color(0xFF334155),
                        ),
                      ),
                      child: Column(
                        children: [
                          Icon(v['icon'] as IconData,
                              color:
                                  isSelected ? Colors.white : const Color(0xFF64748B),
                              size: 24),
                          const SizedBox(height: 4),
                          Text(v['label'] as String,
                              style: TextStyle(
                                  color: isSelected
                                      ? Colors.white
                                      : const Color(0xFF64748B),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500)),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),
            // Slot Selection
            const Text('Select Slot',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _slots.map((slot) {
                final isSelected = _selectedSlot == slot;
                return ChoiceChip(
                  label: Text(slot),
                  selected: isSelected,
                  onSelected: (_) => setState(() => _selectedSlot = slot),
                  selectedColor: const Color(0xFF2563EB),
                  backgroundColor: const Color(0xFF1E293B),
                  side: BorderSide(
                      color: isSelected
                          ? const Color(0xFF2563EB)
                          : const Color(0xFF334155)),
                  labelStyle: TextStyle(
                      color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                      fontWeight: FontWeight.w500),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),
            // Time Selection
            const Text('Duration',
                style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16)),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildTimeSelector(
                    label: 'Start Time',
                    time: _startTime,
                    onTap: () => _pickTime(true),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildTimeSelector(
                    label: 'End Time',
                    time: _endTime,
                    onTap: () => _pickTime(false),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            // Summary
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Column(
                children: [
                  _buildSummaryRow(
                      'Duration', '${_durationHours.toStringAsFixed(1)} hrs'),
                  _buildSummaryRow('Slot', _selectedSlot),
                  _buildSummaryRow(
                      'Rate', '₹${widget.lot?.pricePerHour ?? 30}/hr'),
                  if (_vehicleType == 'ev')
                    _buildSummaryRow('EV Discount', '-10%',
                        color: const Color(0xFF10B981)),
                  const Divider(color: Color(0xFF334155)),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total Amount',
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16)),
                      Text('₹${_totalAmount.toStringAsFixed(0)}',
                          style: const TextStyle(
                              color: Color(0xFF2563EB),
                              fontWeight: FontWeight.bold,
                              fontSize: 20)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isBooking ? null : _confirmBooking,
                child: _isBooking
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Confirm Booking'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeSelector({
    required String label,
    required DateTime time,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF334155)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style:
                    const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}',
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold),
            ),
            Text(
              '${time.day}/${time.month}/${time.year}',
              style:
                  const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value,
      {Color color = const Color(0xFF94A3B8)}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(color: Color(0xFF64748B), fontSize: 14)),
          Text(value,
              style:
                  TextStyle(color: color, fontSize: 14, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildSuccessScreen() {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withOpacity(0.1),
                  shape: BoxShape.circle,
                  border: Border.all(
                      color: const Color(0xFF10B981).withOpacity(0.5),
                      width: 2),
                ),
                child: const Icon(Icons.check_rounded,
                    color: Color(0xFF10B981), size: 56),
              ),
              const SizedBox(height: 24),
              const Text('Booking Confirmed!',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('Slot $_selectedSlot at ${widget.lot?.name ?? "ParkPilot"}',
                  style: const TextStyle(
                      color: Color(0xFF94A3B8), fontSize: 16)),
              const SizedBox(height: 32),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Column(
                  children: [
                    _buildSummaryRow('Booking ID',
                        '#PP${DateTime.now().millisecondsSinceEpoch % 100000}'),
                    _buildSummaryRow('Slot', _selectedSlot),
                    _buildSummaryRow(
                        'Total', '₹${_totalAmount.toStringAsFixed(0)}',
                        color: const Color(0xFF2563EB)),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'A QR ticket has been generated.\nGo to My QR tab to access it.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF64748B), fontSize: 14),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                child: const Text('Back to Home'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
