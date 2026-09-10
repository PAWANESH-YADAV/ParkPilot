import 'package:flutter/material.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _user = _UserProfile(
    name: 'Arjun Sharma',
    email: 'arjun.sharma@email.com',
    phone: '+91 98765 43210',
    vehicle: 'MH12AB3456',
    totalSessions: 47,
    co2SavedKg: 23.4,
    ecoPoints: 840,
    memberSince: 'January 2025',
  );

  final List<EcoBadge> _badges = [
    EcoBadge(name: 'Green Starter', icon: '🌱', earned: true, xp: 100),
    EcoBadge(name: 'EV Champion', icon: '⚡', earned: true, xp: 500),
    EcoBadge(name: 'Carbon Saver', icon: '🌍', earned: true, xp: 1000),
    EcoBadge(name: 'Eco Warrior', icon: '🏆', earned: false, xp: 2000),
    EcoBadge(name: 'Planet Hero', icon: '🚀', earned: false, xp: 5000),
    EcoBadge(name: 'Zero Emission', icon: '♻️', earned: false, xp: 10000),
  ];

  final List<ParkingHistory> _history = [
    ParkingHistory(
      lot: 'ParkPilot Central',
      slot: 'A-01',
      date: '25 Jun 2026',
      duration: '2h 30m',
      amount: 75.0,
      isEV: false,
    ),
    ParkingHistory(
      lot: 'ParkPilot North',
      slot: 'EV-02',
      date: '22 Jun 2026',
      duration: '1h 45m',
      amount: 45.0,
      isEV: true,
    ),
    ParkingHistory(
      lot: 'Smart Park East',
      slot: 'C-12',
      date: '20 Jun 2026',
      duration: '3h 00m',
      amount: 90.0,
      isEV: false,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          _buildSliverHeader(),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _buildStatsRow(),
                const SizedBox(height: 24),
                _buildCarbonCard(),
                const SizedBox(height: 24),
                _buildBadgesSection(),
                const SizedBox(height: 24),
                _buildHistorySection(),
                const SizedBox(height: 24),
                _buildSettingsSection(),
                const SizedBox(height: 32),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSliverHeader() {
    return SliverAppBar(
      expandedHeight: 200,
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
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 36,
                        backgroundColor: Colors.white.withOpacity(0.2),
                        child: Text(
                          _user.name.split(' ').map((n) => n[0]).take(2).join(),
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 24,
                              fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_user.name,
                                style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold)),
                            Text(_user.email,
                                style: const TextStyle(
                                    color: Color(0xFFBFDBFE), fontSize: 13)),
                            const SizedBox(height: 4),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '${_user.ecoPoints} Eco Points',
                                style: const TextStyle(
                                    color: Color(0xFF34D399),
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.edit_outlined,
                            color: Colors.white),
                        onPressed: () {},
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

  Widget _buildStatsRow() {
    return Row(
      children: [
        _buildStatBox('${_user.totalSessions}', 'Sessions', const Color(0xFF2563EB)),
        const SizedBox(width: 12),
        _buildStatBox('${_user.co2SavedKg}kg', 'CO₂ Saved', const Color(0xFF10B981)),
        const SizedBox(width: 12),
        _buildStatBox(_user.memberSince.split(' ')[0], 'Member', const Color(0xFFF59E0B)),
      ],
    );
  }

  Widget _buildStatBox(String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    color: color,
                    fontSize: 20,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(label,
                style: const TextStyle(
                    color: Color(0xFF64748B), fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildCarbonCard() {
    final nextBadge = _badges.firstWhere((b) => !b.earned);
    final progress = _user.ecoPoints / nextBadge.xp;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF064E3B), Color(0xFF065F46)],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.eco_rounded, color: Color(0xFF34D399), size: 20),
              SizedBox(width: 8),
              Text('Carbon Footprint',
                  style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildCarbonStat('${_user.co2SavedKg} kg', 'CO₂ Saved'),
              _buildCarbonStat(
                  '${(_user.co2SavedKg * 0.04).toStringAsFixed(1)}',
                  'Trees Equiv.'),
              _buildCarbonStat('${_user.ecoPoints}', 'Eco Points'),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Next: ${nextBadge.icon} ${nextBadge.name}',
                  style: const TextStyle(
                      color: Color(0xFF6EE7B7), fontSize: 13)),
              Text('${_user.ecoPoints}/${nextBadge.xp} XP',
                  style: const TextStyle(
                      color: Color(0xFF6EE7B7), fontSize: 13)),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress.clamp(0.0, 1.0),
              backgroundColor: const Color(0xFF064E3B),
              valueColor:
                  const AlwaysStoppedAnimation<Color>(Color(0xFF34D399)),
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCarbonStat(String value, String label) {
    return Column(
      children: [
        Text(value,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold)),
        Text(label,
            style:
                const TextStyle(color: Color(0xFF6EE7B7), fontSize: 12)),
      ],
    );
  }

  Widget _buildBadgesSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Eco Badges',
            style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18)),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 1.0,
          ),
          itemCount: _badges.length,
          itemBuilder: (_, i) {
            final badge = _badges[i];
            return Container(
              decoration: BoxDecoration(
                color: badge.earned
                    ? const Color(0xFF1E293B)
                    : const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: badge.earned
                      ? const Color(0xFF10B981).withOpacity(0.5)
                      : const Color(0xFF1E293B),
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    badge.icon,
                    style: TextStyle(
                      fontSize: 28,
                      color: badge.earned ? null : const Color(0xFF334155),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    badge.name,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: badge.earned
                          ? Colors.white
                          : const Color(0xFF475569),
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    '${badge.xp} XP',
                    style: TextStyle(
                        color: badge.earned
                            ? const Color(0xFF10B981)
                            : const Color(0xFF334155),
                        fontSize: 9),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildHistorySection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Recent History',
            style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18)),
        const SizedBox(height: 12),
        ..._history.map((h) => _buildHistoryItem(h)),
      ],
    );
  }

  Widget _buildHistoryItem(ParkingHistory h) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: h.isEV
                  ? const Color(0xFF10B981).withOpacity(0.1)
                  : const Color(0xFF2563EB).withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
                h.isEV ? Icons.electric_car_rounded : Icons.directions_car_rounded,
                color: h.isEV
                    ? const Color(0xFF10B981)
                    : const Color(0xFF2563EB),
                size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(h.lot,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 14)),
                Text('${h.date} • ${h.duration} • Slot ${h.slot}',
                    style: const TextStyle(
                        color: Color(0xFF64748B), fontSize: 12)),
              ],
            ),
          ),
          Text('₹${h.amount.toStringAsFixed(0)}',
              style: const TextStyle(
                  color: Color(0xFF2563EB),
                  fontWeight: FontWeight.bold,
                  fontSize: 16)),
        ],
      ),
    );
  }

  Widget _buildSettingsSection() {
    final settingsItems = [
      (Icons.notifications_outlined, 'Notifications', ''),
      (Icons.language_outlined, 'Language', 'English'),
      (Icons.lock_outline_rounded, 'Change Password', ''),
      (Icons.help_outline_rounded, 'Help & Support', ''),
      (Icons.logout_rounded, 'Log Out', ''),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Settings',
            style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 18)),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF334155)),
          ),
          child: Column(
            children: settingsItems.asMap().entries.map((entry) {
              final i = entry.key;
              final item = entry.value;
              final isLast = i == settingsItems.length - 1;
              final isLogout = item.$1 == Icons.logout_rounded;

              return Column(
                children: [
                  ListTile(
                    leading: Icon(item.$1,
                        color: isLogout
                            ? const Color(0xFFEF4444)
                            : const Color(0xFF64748B),
                        size: 22),
                    title: Text(item.$2,
                        style: TextStyle(
                            color: isLogout
                                ? const Color(0xFFEF4444)
                                : Colors.white,
                            fontSize: 14)),
                    trailing: item.$3.isEmpty
                        ? const Icon(Icons.chevron_right_rounded,
                            color: Color(0xFF475569))
                        : Text(item.$3,
                            style: const TextStyle(
                                color: Color(0xFF64748B), fontSize: 12)),
                    onTap: () {},
                  ),
                  if (!isLast)
                    const Divider(
                        height: 1, color: Color(0xFF1E293B), indent: 56),
                ],
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}

class _UserProfile {
  final String name;
  final String email;
  final String phone;
  final String vehicle;
  final int totalSessions;
  final double co2SavedKg;
  final int ecoPoints;
  final String memberSince;

  const _UserProfile({
    required this.name,
    required this.email,
    required this.phone,
    required this.vehicle,
    required this.totalSessions,
    required this.co2SavedKg,
    required this.ecoPoints,
    required this.memberSince,
  });
}

class EcoBadge {
  final String name;
  final String icon;
  final bool earned;
  final int xp;
  const EcoBadge(
      {required this.name,
      required this.icon,
      required this.earned,
      required this.xp});
}

class ParkingHistory {
  final String lot;
  final String slot;
  final String date;
  final String duration;
  final double amount;
  final bool isEV;
  const ParkingHistory({
    required this.lot,
    required this.slot,
    required this.date,
    required this.duration,
    required this.amount,
    required this.isEV,
  });
}
