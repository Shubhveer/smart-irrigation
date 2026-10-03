import 'package:flutter/material.dart';

void main() {
  runApp(const FarmSaathiApp());
}

class FarmSaathiApp extends StatelessWidget {
  const FarmSaathiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Farm Saathi',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF4F6F1),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2F6B3C),
        ),
        fontFamily: 'sans',
      ),
      home: const FarmSaathiHome(),
    );
  }
}

class FarmSaathiHome extends StatelessWidget {
  const FarmSaathiHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 16, 18, 30),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              // ==================================================
              // HEADER
              // ==================================================

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [

                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        'Farm Saathi',
                        style: TextStyle(
                          fontSize: 27,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF17351F),
                        ),
                      ),
                      SizedBox(height: 3),
                      Text(
                        'Smart guidance for your farm',
                        style: TextStyle(
                          fontSize: 13,
                          color: Color(0xFF69736C),
                        ),
                      ),
                    ],
                  ),

                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 13,
                      vertical: 9,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE3EDE2),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: const Row(
                      children: [
                        Icon(
                          Icons.location_on_outlined,
                          size: 16,
                          color: Color(0xFF2F6B3C),
                        ),
                        SizedBox(width: 5),
                        Text(
                          'Nagpur',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF2F6B3C),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // ==================================================
              // FARM STATUS CARD
              // ==================================================

              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF285F37),
                      Color(0xFF3F7B4B),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(22),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.green.withOpacity(0.18),
                      blurRadius: 18,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [

                    const Row(
                      mainAxisAlignment:
                          MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'TODAY',
                          style: TextStyle(
                            color: Color(0xFFD8E8D8),
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.2,
                          ),
                        ),
                        Text(
                          'Nagpur',
                          style: TextStyle(
                            color: Color(0xFFD8E8D8),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 15),

                    const Text(
                      'Good farming starts\nwith good decisions.',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        height: 1.2,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 18),

                    Row(
                      children: [

                        _StatusItem(
                          value: '28°C',
                          label: 'Temperature',
                        ),

                        const SizedBox(width: 28),

                        _StatusItem(
                          value: '62%',
                          label: 'Humidity',
                        ),

                        const SizedBox(width: 28),

                        _StatusItem(
                          value: 'Good',
                          label: 'Farm status',
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 25),

              // ==================================================
              // TODAY'S ACTION
              // ==================================================

              const Text(
                'What should I do today?',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF18251C),
                ),
              ),

              const SizedBox(height: 6),

              const Text(
                'Quick guidance based on your farm information',
                style: TextStyle(
                  fontSize: 13,
                  color: Color(0xFF707870),
                ),
              ),

              const SizedBox(height: 15),

              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(17),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(17),
                  border: Border.all(
                    color: const Color(0xFFE0E5DE),
                  ),
                ),
                child: Row(
                  children: [

                    Container(
                      width: 5,
                      height: 58,
                      decoration: BoxDecoration(
                        color: const Color(0xFFE0A82E),
                        borderRadius: BorderRadius.circular(5),
                      ),
                    ),

                    const SizedBox(width: 14),

                    const Expanded(
                      child: Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Check irrigation',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          SizedBox(height: 5),
                          Text(
                            'Review soil moisture and today’s weather before irrigating.',
                            style: TextStyle(
                              fontSize: 13,
                              height: 1.35,
                              color: Color(0xFF707870),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const Text(
                      '›',
                      style: TextStyle(
                        fontSize: 28,
                        color: Color(0xFF7C857D),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),

              // ==================================================
              // QUICK ACTIONS
              // ==================================================

              const Text(
                'Quick actions',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF18251C),
                ),
              ),

              const SizedBox(height: 14),

              Row(
                children: [

                  Expanded(
                    child: _QuickAction(
                      title: 'Irrigation',
                      subtitle: 'Water advice',
                      color: const Color(0xFFE4F0F4),
                      textColor: const Color(0xFF246174),
                      onTap: () {},
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: _QuickAction(
                      title: 'Weather',
                      subtitle: 'Local forecast',
                      color: const Color(0xFFE9EFE4),
                      textColor: const Color(0xFF376340),
                      onTap: () {},
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 12),

              Row(
                children: [

                  Expanded(
                    child: _QuickAction(
                      title: 'Plant Check',
                      subtitle: 'Take a photo',
                      color: const Color(0xFFF0EBDD),
                      textColor: const Color(0xFF80632A),
                      onTap: () {},
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: _QuickAction(
                      title: 'Soil',
                      subtitle: 'Soil guidance',
                      color: const Color(0xFFEDE8E2),
                      textColor: const Color(0xFF6A5139),
                      onTap: () {},
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 28),

              // ==================================================
              // FARM TOOLS
              // ==================================================

              const Text(
                'Farm tools',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF18251C),
                ),
              ),

              const SizedBox(height: 14),

              _ToolTile(
                title: 'Crop Health',
                description:
                    'Understand crop symptoms and possible causes',
                onTap: () {},
              ),

              _ToolTile(
                title: 'Fertilizer Guidance',
                description:
                    'Use crop stage and soil test information',
                onTap: () {},
              ),

              _ToolTile(
                title: 'Pest Guide',
                description:
                    'Learn about common crop pests',
                onTap: () {},
              ),

              _ToolTile(
                title: 'Government Agriculture News',
                description:
                    'Official schemes, advisories and announcements',
                onTap: () {},
              ),

              const SizedBox(height: 22),

              // ==================================================
              // LANGUAGE
              // ==================================================

              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  vertical: 14,
                ),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: const Color(0xFFE0E5DE),
                  ),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'English',
                      style: TextStyle(
                        color: Color(0xFF2F6B3C),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      '   •   ',
                      style: TextStyle(
                        color: Color(0xFFB2B8B2),
                      ),
                    ),
                    Text(
                      'हिन्दी',
                      style: TextStyle(
                        color: Color(0xFF2F6B3C),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      '   •   ',
                      style: TextStyle(
                        color: Color(0xFFB2B8B2),
                      ),
                    ),
                    Text(
                      'मराठी',
                      style: TextStyle(
                        color: Color(0xFF2F6B3C),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


// ============================================================
// STATUS ITEM
// ============================================================

class _StatusItem extends StatelessWidget {
  final String value;
  final String label;

  const _StatusItem({
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 17,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFFD5E4D6),
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}


// ============================================================
// QUICK ACTION
// ============================================================

class _QuickAction extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;
  final Color textColor;
  final VoidCallback onTap;

  const _QuickAction({
    required this.title,
    required this.subtitle,
    required this.color,
    required this.textColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(17),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(17),
        child: Padding(
          padding: const EdgeInsets.all(17),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  color: textColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                subtitle,
                style: TextStyle(
                  color: textColor.withOpacity(0.75),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 14),
              Align(
                alignment: Alignment.bottomRight,
                child: Text(
                  'Open →',
                  style: TextStyle(
                    color: textColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


// ============================================================
// FARM TOOL
// ============================================================

class _ToolTile extends StatelessWidget {
  final String title;
  final String description;
  final VoidCallback onTap;

  const _ToolTile({
    required this.title,
    required this.description,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(15),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 17,
              vertical: 16,
            ),
            child: Row(
              children: [

                Container(
                  width: 4,
                  height: 45,
                  decoration: BoxDecoration(
                    color: const Color(0xFF3B7546),
                    borderRadius: BorderRadius.circular(5),
                  ),
                ),

                const SizedBox(width: 14),

                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF1C281F),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: const TextStyle(
                          fontSize: 12.5,
                          color: Color(0xFF737A74),
                        ),
                      ),
                    ],
                  ),
                ),

                const Text(
                  '›',
                  style: TextStyle(
                    fontSize: 25,
                    color: Color(0xFF89918A),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
