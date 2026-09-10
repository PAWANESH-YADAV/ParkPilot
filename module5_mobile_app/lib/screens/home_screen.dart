import 'package:flutter/material.dart';
import 'booking_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Mock data for parking lots
  final List<ParkingLot> _lots = [
    ParkingLot(
      id: 1,
      name: 'ParkPilot Central',
      address: 'MG Road, Bengaluru',
      available: 23,
      total: 50,
      pricePerHour: 30,
      distance: '0.3 km',
      hasEV: true,
      rating: 4.8,
    ),
    ParkingLot(
      id: 2,
      name: 'ParkPilot North',
      address: 'Bandra, Mumbai',
      available: 8,
      total: 30,
      pricePerHour: 35,
      distance: '1.2 km',
      hasEV: false,
      rating: 4.5,
    ),
    ParkingLot(
      id: 3,
      name: 'Smart Park East',
      address: 'Koramangala, Bengaluru',
      available: 0,
      total: 20,
      pricePerHour: 25,
      distance: '2.1 km',
      hasEV: true,
      rating: 4.2,
    ),
  ];

  final _searchController = TextEditingController();
  String _filter = 'All';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          _buildSliverAppBar(),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _buildSearchBar(),
                const SizedBox(height: 16),
                _buildQuickStats(),
                const SizedBox(height: 24),
                _buildFilterChips(),
                const SizedBox(height: 16),
                const Text(
                  'Nearby Parking',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                ..._lots
                    .where((lot) =>
                        (_filter == 'All' ||
                            (_filter == 'EV' && lot.hasEV) ||
                            (_filter == 'Available' && lot.available > 0)) &&
                        lot.name
                            .toLowerCase()
                            .contains(_searchController.text.toLowerCase()))
                    .map((lot) => _buildLotCard(lot)),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      expandedHeight: 140,
      pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF1E3A8A), Color(0xFF7C3AED)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Good Morning! 👋',
                            style: TextStyle(color: Color(0xFFBFDBFE), fontSize: 14),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Find Your Spot',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.notifications_outlined,
                            color: Colors.white),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSearchBar() {
    return TextField(
      controller: _searchController,
      onChanged: (_) => setState(() {}),
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: 'Search parking lots...',
        prefixIcon: const Icon(Icons.search, color: Color(0xFF64748B)),
        suffixIcon: _searchController.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear, color: Color(0xFF64748B)),
                onPressed: () {
                  _searchController.clear();
                  setState(() {});
                },
              )
            : null,
      ),
    );
  }

  Widget _buildQuickStats() {
    return Row(
      children: [
        _buildStatCard(Icons.local_parking_rounded, '150', 'Total Slots',
            const Color(0xFF2563EB)),
        const SizedBox(width: 12),
        _buildStatCard(Icons.check_circle_outline_rounded, '31', 'Available',
            const Color(0xFF10B981)),
        const SizedBox(width: 12),
        _buildStatCard(
            Icons.bolt_rounded, '8', 'EV Chargers', const Color(0xFFF59E0B)),
      ],
    );
  }

  Widget _buildStatCard(
      IconData icon, String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 8),
            Text(value,
                style: TextStyle(
                    color: color, fontSize: 20, fontWeight: FontWeight.bold)),
            Text(label,
                style:
                    const TextStyle(color: Color(0xFF64748B), fontSize: 11)),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChips() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: ['All', 'Available', 'EV', 'Nearby'].map((filter) {
          final isSelected = _filter == filter;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(filter),
              selected: isSelected,
              onSelected: (_) => setState(() => _filter = filter),
              selectedColor: const Color(0xFF2563EB),
              checkmarkColor: Colors.white,
              labelStyle: TextStyle(
                  color: isSelected ? Colors.white : const Color(0xFF94A3B8)),
              backgroundColor: const Color(0xFF1E293B),
              side: BorderSide(
                  color: isSelected
                      ? const Color(0xFF2563EB)
                      : const Color(0xFF334155)),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildLotCard(ParkingLot lot) {
    final occupancyPct = 1 - (lot.available / lot.total);
    final statusColor = lot.available == 0
        ? const Color(0xFFEF4444)
        : lot.available < 5
            ? const Color(0xFFF59E0B)
            : const Color(0xFF10B981);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          if (lot.available > 0) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => BookingScreen(lot: lot)),
            );
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content: Text('No slots available at this location')),
            );
          }
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              lot.name,
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold),
                            ),
                            if (lot.hasEV) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF10B981).withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(
                                      color: const Color(0xFF10B981)
                                          .withOpacity(0.5)),
                                ),
                                child: const Row(
                                  children: [
                                    Icon(Icons.bolt, color: Color(0xFF10B981), size: 10),
                                    SizedBox(width: 2),
                                    Text('EV',
                                        style: TextStyle(
                                            color: Color(0xFF10B981),
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.location_on_outlined,
                                size: 14, color: Color(0xFF64748B)),
                            const SizedBox(width: 4),
                            Text(lot.address,
                                style: const TextStyle(
                                    color: Color(0xFF64748B), fontSize: 12)),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '₹${lot.pricePerHour}/hr',
                        style: const TextStyle(
                            color: Color(0xFF2563EB),
                            fontSize: 16,
                            fontWeight: FontWeight.bold),
                      ),
                      Text(
                        lot.distance,
                        style: const TextStyle(
                            color: Color(0xFF64748B), fontSize: 12),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.local_parking_rounded,
                      size: 14, color: statusColor),
                  const SizedBox(width: 4),
                  Text(
                    '${lot.available} available',
                    style: TextStyle(color: statusColor, fontSize: 12),
                  ),
                  const SizedBox(width: 8),
                  Text('of ${lot.total} total',
                      style: const TextStyle(
                          color: Color(0xFF64748B), fontSize: 12)),
                  const Spacer(),
                  Row(
                    children: [
                      const Icon(Icons.star_rounded,
                          size: 14, color: Color(0xFFF59E0B)),
                      const SizedBox(width: 2),
                      Text(lot.rating.toString(),
                          style: const TextStyle(
                              color: Color(0xFF94A3B8), fontSize: 12)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: occupancyPct,
                  backgroundColor: const Color(0xFF334155),
                  valueColor: AlwaysStoppedAnimation<Color>(statusColor),
                  minHeight: 6,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Data Model ────────────────────────────────────────────────────────────────

class ParkingLot {
  final int id;
  final String name;
  final String address;
  final int available;
  final int total;
  final double pricePerHour;
  final String distance;
  final bool hasEV;
  final double rating;

  const ParkingLot({
    required this.id,
    required this.name,
    required this.address,
    required this.available,
    required this.total,
    required this.pricePerHour,
    required this.distance,
    required this.hasEV,
    required this.rating,
  });
}
