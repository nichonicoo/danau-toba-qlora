import json
import random
from datetime import date, timedelta

# ============================================================
# SYSTEM PROMPTS (copied from existing dataset)
# ============================================================

BMKG_SYSTEM_PREFIX = """Kamu adalah AI Prakiraan Cuaca Indonesia. Tugasmu adalah menyampaikan kondisi cuaca dari TOOL_RESULT kepada pengguna secara ramah, informatif, dan praktis. 

Aturan Penulisan (Wajib Ikuti Format Struktur Ini):
[Berikan salam hangat pembuka yang ramah, lalu sebutkan lokasi daerah berdasarkan data 'location']

Kondisi Cuaca Terkini:
- **Status Cuaca**: [Sebutkan info 'forecast', misal: Cerah Berawan / Hujan Ringan]
- **Suhu Udara**: [Angka dari 'temperature_c']°C
- **Kelembaban**: [Angka dari 'humidity_percent']%
- **Kecepatan Angin**: [Angka dari 'wind_speed_knots'] knots

Rekomendasi Praktis Wisatawan:
- **Pakaian yang Cocok**: [Gunakan proses berpikir internalmu untuk merekomendasikan tipe baju yang pas dengan suhu dan status cuaca di atas]
- **Perlengkapan Wajib**: [Sebutkan alat bantu wajib secara logis, misal: payung/jas hujan jika hujan, atau kacamata hitam/sunscreen jika cerah]

TOOL_RESULT:
"""

FLIGHT_SYSTEM_PREFIX = """Kamu adalah AI Ekstraktor Data Penerbangan. Tugasmu adalah menampilkan SEMUA opsi penerbangan dari TOOL_RESULT secara lengkap dan terstruktur. Jangan merangkum atau melewatkan data.

====================
FORMAT OUTPUT (WAJIB)
====================

Pesawat yang tersedia dari Bandara [departure_airport_id] ke Bandara [arrival_airport_id] pada tanggal [departure_date] - [arrival_date] terdapat [jumlah penerbangan] penerbangan:

Untuk setiap penerbangan:

- **[airline] ([flight_number])**
  Jam: [HH:MM dari departure_time] - [HH:MM dari arrival_time]
  Kelas: [travel_class]
  Harga: [Jika price_idr null → "Rp -", jika ada → format Rupiah dengan titik]
  Detail: Menggunakan pesawat [airplane], [extensions yang sudah diinterpretasikan]

====================
ATURAN TAMBAHAN
====================

- Ambil hanya jam (HH:MM) dari waktu (contoh: 2026-09-10 08:20 → 08:20)
- Format harga ke Rupiah dengan pemisah ribuan titik (contoh: 3312300 → 3.312.300)
- Interpretasi extensions:
  - "Below average legroom" → "Ruang kaki sempit"
  - "Average legroom" → "Ruang kaki standar"
  - "Above average legroom" → "Ruang kaki luas"
  - "Carbon emissions estimate" → "Estimasi emisi karbon"
  - "On-demand video" → "Hiburan di pesawat tersedia"
  - "In-seat USB outlet" → "Colokan USB tersedia"
  - "Stream media to your device" → "Streaming media ke perangkat"
- Jika extensions kosong → "Informasi tambahan tidak tersedia"
- Jangan mengubah nilai data
- Tampilkan semua penerbangan tanpa terlewat
- Jangan menambahkan penomoran seperti "1.", "2.", dst.
- Gunakan format bullet "-" sesuai instruksi.

TOOL_RESULT:
"""

HOTEL_SYSTEM_PREFIX = """Kamu adalah AI Travel Planner yang menampilkan rekomendasi hotel berdasarkan TOOL_RESULT.

====================
FORMAT OUTPUT (WAJIB)
====================

1. Pembuka:
- Jika tersedia check_in_date & check_out_date:
  "Berikut adalah beberapa rekomendasi hotel di [Lokasi] untuk masa inap [check_in_date] - [check_out_date] ([jumlah_malam] malam)"
- Jika tidak tersedia:
  "Berikut adalah beberapa rekomendasi hotel di [Lokasi]"

2. Jumlah hotel:
"Hotel yang tersedia ada [jumlah hotel]:"

3. Format tiap hotel:

- **[name]**
  Rating: [rating/5 atau 'Belum ada rating'] ([reviews] ulasan)
  Estimasi Harga per Malam: Rp [price_per_night, format ribuan titik]
  Total Harga: Rp [total_price, format ribuan titik]
  Waktu Check-In: [check_in atau 'Belum ada waktu']
  Waktu Check-Out: [check_out atau 'Belum ada waktu']
  Fasilitas: [amenities dipisahkan koma atau 'Fasilitas standar akomodasi']
  Tempat Terdekat: [nearby dipisahkan koma]

====================
ATURAN TAMBAHAN
====================

- Format angka ke Rupiah dengan pemisah ribuan titik (contoh: 1818630 → 1.818.630)
- Jumlah hotel harus sesuai dengan jumlah data pada TOOL_RESULT.
- Jangan mengubah nilai angka
- Tampilkan semua hotel tanpa terlewat
- Interpretasi fasilitas:
  - Jika suatu fasilitas mengandung "($)", artinya berbayar.
  - Hapus simbol "($)" dan tambahkan keterangan "(berbayar)".
  Contoh:
  - "Breakfast ($)" → "Sarapan (berbayar)"
  - "Parking ($)" → "Parkir (berbayar)"
  - Jika tidak ada "($)", tampilkan tanpa perubahan.

TOOL_RESULT:
"""

# ============================================================
# DATA POOLS
# ============================================================

WEATHER_STATUSES = [
    "Cerah", "Cerah Berawan", "Berawan", "Berawan Tebal",
    "Hujan Ringan", "Hujan Sedang", "Hujan Lebat",
    "Hujan Petir", "Kabut", "Asap"
]

CITIES_BMKG = [
    # Existing 45 + new ones
    "Jakarta", "Tangerang", "Bekasi", "Depok", "Bogor",
    "Bandung", "Cimahi", "Sukabumi", "Tasikmalaya", "Cirebon",
    "Semarang", "Solo", "Salatiga", "Pekalongan", "Tegal",
    "Purwokerto", "Magelang", "Klaten", "Kudus", "Jepara",
    "Surabaya", "Malang", "Sidoarjo", "Gresik", "Pasuruan",
    "Mojokerto", "Jombang", "Kediri", "Blitar", "Madiun",
    "Batu", "Probolinggo", "Jember", "Banyuwangi", "Situbondo",
    "Tulungagung", "Trenggalek", "Ponorogo", "Ngawi", "Magetan",
    "Nganjuk", "Lamongan", "Tuban", "Bojonegoro", "Bangkalan",
    "Pamekasan", "Sumenep", "Sampang", "Bondowoso",
    "Medan", "Pekanbaru", "Padang", "Palembang", "Bandar Lampung",
    "Jambi", "Bengkulu", "Pangkal Pinang", "Tanjung Pinang",
    "Pontianak", "Banjarmasin", "Samarinda", "Balikpapan",
    "Palangkaraya", "Tarakan", "Nunukan",
    "Makassar", "Manado", "Palu", "Kendari", "Gorontalo",
    "Ambon", "Ternate", "Sorong", "Manokwari", "Jayapura",
    "Denpasar", "Mataram", "Kupang", "Labuan Bajo", "Ende",
    "Wamena", "Merauke", "Timika", "Nabire",
    "Banda Aceh", "Lhokseumawe", "Langkat", "Pematangsiantar",
    "Yogyakarta", "Sleman", "Bantul",
]
# Remove already existing
EXISTING_BMKG = {
    "Ambon","Balikpapan","Bandar Lampung","Bandung","Banjar","Banjarmasin",
    "Batu","Bekasi","Bengkulu","Blitar","Bogor","Cimahi","Cirebon","Denpasar",
    "Depok","Jambi","Jayapura","Kediri","Kupang","Madiun","Magelang","Malang",
    "Manado","Mataram","Medan","Mojokerto","Padang","Palangkaraya","Palembang",
    "Pangkal Pinang","Pasuruan","Pekalongan","Pekanbaru","Pontianak","Probolinggo",
    "Salatiga","Semarang","Sukabumi","Surabaya","Surakarta","Tanjung Pinang","Tasikmalaya","Yogyakarta"
}
NEW_BMKG_CITIES = [c for c in CITIES_BMKG if c not in EXISTING_BMKG]

BMKG_QUERIES = [
    "Bagaimana cuaca di {}?",
    "Cuaca {} hari ini gimana?",
    "Info cuaca {} sekarang dong",
    "Cek cuaca {}",
    "Prakiraan cuaca {} hari ini",
    "Kondisi cuaca di {} saat ini",
    "Gimana cuaca {} hari ini?",
    "Cuaca {} sekarang?",
]

ADM4_MAP = {
    "Jakarta": "31.71.01.1001", "Tangerang": "36.71.01.1001",
    "Bekasi": "32.75.01.1001", "Depok": "32.76.01.1001",
    "Bogor": "32.71.01.1001", "Bandung": "32.73.01.1001",
    "Cimahi": "32.77.01.1001", "Sukabumi": "32.72.01.1001",
    "Tasikmalaya": "32.78.01.1001", "Cirebon": "32.74.01.1001",
    "Semarang": "33.74.01.1001", "Solo": "33.72.01.1001",
    "Salatiga": "33.73.01.1001", "Pekalongan": "33.75.01.1001",
    "Tegal": "33.76.01.1001", "Purwokerto": "33.02.01.1001",
    "Magelang": "33.71.01.1001", "Klaten": "33.10.01.1001",
    "Kudus": "33.19.01.1001", "Jepara": "33.20.01.1001",
    "Surabaya": "35.78.01.1001", "Malang": "35.73.01.1001",
    "Sidoarjo": "35.15.01.1001", "Gresik": "35.25.01.1001",
    "Pasuruan": "35.74.01.1001", "Mojokerto": "35.76.01.1001",
    "Jombang": "35.17.01.1001", "Kediri": "35.71.01.1001",
    "Blitar": "35.72.01.1001", "Madiun": "35.77.01.1001",
    "Batu": "35.79.01.1001", "Probolinggo": "35.75.01.1001",
    "Jember": "35.09.01.1001", "Banyuwangi": "35.10.01.1001",
    "Situbondo": "35.12.01.1001", "Tulungagung": "35.04.01.1001",
    "Trenggalek": "35.03.01.1001", "Ponorogo": "35.02.01.1001",
    "Ngawi": "35.21.01.1001", "Magetan": "35.22.01.1001",
    "Nganjuk": "35.18.01.1001", "Lamongan": "35.24.01.1001",
    "Tuban": "35.23.01.1001", "Bojonegoro": "35.22.01.1001",
    "Bangkalan": "35.26.01.1001", "Pamekasan": "35.28.01.1001",
    "Sumenep": "35.29.01.1001", "Sampang": "35.27.01.1001",
    "Bondowoso": "35.11.01.1001", "Medan": "12.71.01.1001",
    "Pekanbaru": "14.71.01.1001", "Padang": "13.71.01.1001",
    "Palembang": "16.71.01.1001", "Bandar Lampung": "18.71.01.1001",
    "Jambi": "15.71.01.1001", "Bengkulu": "17.71.01.1001",
    "Pangkal Pinang": "19.71.01.1001", "Tanjung Pinang": "21.71.01.1001",
    "Pontianak": "61.71.01.1001", "Banjarmasin": "63.71.01.1001",
    "Samarinda": "64.72.01.1001", "Balikpapan": "64.71.01.1001",
    "Palangkaraya": "62.71.01.1001", "Tarakan": "65.72.01.1001",
    "Nunukan": "65.07.01.1001", "Makassar": "73.71.01.1001",
    "Manado": "71.71.01.1001", "Palu": "72.71.01.1001",
    "Kendari": "74.71.01.1001", "Gorontalo": "75.71.01.1001",
    "Ambon": "81.71.01.1001", "Ternate": "82.71.01.1001",
    "Sorong": "95.72.01.1001", "Manokwari": "96.71.01.1001",
    "Jayapura": "94.71.01.1001", "Denpasar": "51.71.01.1001",
    "Mataram": "52.71.01.1001", "Kupang": "53.71.01.1001",
    "Labuan Bajo": "53.03.14.2001", "Ende": "53.06.01.1001",
    "Wamena": "91.03.01.1001", "Merauke": "91.71.01.1001",
    "Timika": "91.04.01.1001", "Nabire": "91.06.01.1001",
    "Banda Aceh": "11.71.01.1001", "Lhokseumawe": "11.72.01.1001",
    "Langkat": "12.08.01.1001", "Pematangsiantar": "12.72.01.1001",
    "Yogyakarta": "34.71.01.1001", "Sleman": "34.04.01.1001",
    "Bantul": "34.02.01.1001",
}

NOT_FOUND_CITIES = [
    "Ujung Kulon", "Gunung Bromo", "Raja Ampat", "Wakatobi",
    "Ora Beach", "Pulau Komodo", "Togean", "Nias",
    "Sabang", "Belitung Timur", "Pulau Tidung",
]

AMBIGUOUS_CITIES = {
    "Lombok": ["Lombok Barat", "Lombok Tengah", "Lombok Timur", "Lombok Utara"],
    "Flores": ["Flores Timur", "Manggarai Barat", "Ende", "Ngada"],
    "Kalimantan": ["Kalimantan Barat", "Kalimantan Timur", "Kalimantan Selatan", "Kalimantan Tengah"],
    "Sulawesi": ["Sulawesi Selatan", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Tenggara"],
    "Papua": ["Papua Barat", "Papua Tengah", "Papua Selatan", "Papua Pegunungan"],
    "Sumatra": ["Sumatera Utara", "Sumatera Barat", "Sumatera Selatan"],
    "Maluku": ["Maluku Tengah", "Maluku Tenggara", "Maluku Utara"],
    "Borneo": ["Kalimantan Barat", "Kalimantan Timur", "Kalimantan Selatan"],
    "Nusa Tenggara": ["NTB - Mataram", "NTT - Kupang", "Lombok", "Flores"],
    "Lembata": ["Lembata Barat", "Lembata Timur"],
    "Bima": ["Kota Bima", "Kabupaten Bima"],
    "Poso": ["Kabupaten Poso", "Kota Poso"],
}

# Flight data pools
AIRLINES = [
    ("Garuda Indonesia", "GA", ["Boeing 737", "Airbus A330", "Boeing 777"]),
    ("Lion Air", "JT", ["Boeing 737", "Boeing 737 MAX"]),
    ("Citilink", "QG", ["Airbus A320", "Airbus A320neo"]),
    ("Indonesia AirAsia", "QZ", ["Airbus A320", "Airbus A320neo"]),
    ("Batik Air", "ID", ["Boeing 737", "Airbus A320", "Airbus A330"]),
    ("Nam Air", "IN", ["Boeing 737"]),
    ("Sriwijaya Air", "SJ", ["Boeing 737"]),
    ("TransNusa", "8B", ["ATR 72", "Airbus A320"]),
    ("Wings Air", "IW", ["ATR 72"]),
]

ROUTES = [
    # Existing routes excluded: CGK->DPS, CGK->KNO, CGK->MLG, CGK->YIA, CGK->MDC, CGK->LOP
    # DPS->CGK, DPS->LBJ, DPS->LOP, SUB->DPS, SUB->UPG
    # BPN->SUB, BPN->YIA, UPG->CGK, UPG->LOP, UPG->MDC, UPG->YIA
    ("CGK", "SUB", "Jakarta", "Surabaya", 75),
    ("CGK", "UPG", "Jakarta", "Makassar", 110),
    ("CGK", "BPN", "Jakarta", "Balikpapan", 120),
    ("CGK", "PLM", "Jakarta", "Palembang", 60),
    ("CGK", "PKU", "Jakarta", "Pekanbaru", 90),
    ("CGK", "PDG", "Jakarta", "Padang", 90),
    ("CGK", "AMQ", "Jakarta", "Ambon", 210),
    ("CGK", "KOE", "Jakarta", "Kupang", 180),
    ("CGK", "BIK", "Jakarta", "Biak", 270),
    ("CGK", "SOC", "Jakarta", "Solo", 70),
    ("CGK", "SRG", "Jakarta", "Semarang", 65),
    ("CGK", "TRK", "Jakarta", "Tarakan", 150),
    ("SUB", "CGK", "Surabaya", "Jakarta", 75),
    ("SUB", "BPN", "Surabaya", "Balikpapan", 85),
    ("SUB", "MDC", "Surabaya", "Manado", 130),
    ("SUB", "LBJ", "Surabaya", "Labuan Bajo", 95),
    ("SUB", "KOE", "Surabaya", "Kupang", 110),
    ("SUB", "AMQ", "Surabaya", "Ambon", 130),
    ("DPS", "SUB", "Denpasar", "Surabaya", 55),
    ("DPS", "MDC", "Denpasar", "Manado", 120),
    ("DPS", "UPG", "Denpasar", "Makassar", 80),
    ("DPS", "AMQ", "Denpasar", "Ambon", 140),
    ("DPS", "KOE", "Denpasar", "Kupang", 80),
    ("UPG", "DPS", "Makassar", "Denpasar", 80),
    ("UPG", "AMQ", "Makassar", "Ambon", 90),
    ("UPG", "KDI", "Makassar", "Kendari", 55),
    ("UPG", "PLW", "Makassar", "Palu", 60),
    ("KNO", "CGK", "Medan", "Jakarta", 130),
    ("KNO", "SUB", "Medan", "Surabaya", 165),
    ("KNO", "DPS", "Medan", "Denpasar", 190),
    ("BPN", "MDC", "Balikpapan", "Manado", 90),
    ("BPN", "CGK", "Balikpapan", "Jakarta", 120),
    ("MDC", "UPG", "Manado", "Makassar", 90),
    ("MDC", "CGK", "Manado", "Jakarta", 200),
    ("PLM", "CGK", "Palembang", "Jakarta", 60),
    ("PLM", "DPS", "Palembang", "Denpasar", 110),
    ("JOG", "CGK", "Yogyakarta", "Jakarta", 60),
    ("JOG", "SUB", "Yogyakarta", "Surabaya", 55),
    ("JOG", "DPS", "Yogyakarta", "Denpasar", 75),
    ("LBJ", "CGK", "Labuan Bajo", "Jakarta", 140),
    ("LBJ", "SUB", "Labuan Bajo", "Surabaya", 95),
    ("LBJ", "DPS", "Labuan Bajo", "Denpasar", 60),
]

EXTENSIONS_POOL = [
    ["Below average legroom (29 in)", "Carbon emissions estimate: 88 kg"],
    ["Below average legroom (28 in)", "Carbon emissions estimate: 96 kg"],
    ["Average legroom (31 in)", "Carbon emissions estimate: 107 kg"],
    ["Average legroom (31 in)", "On-demand video", "Carbon emissions estimate: 112 kg"],
    ["Above average legroom (32 in)", "In-seat USB outlet", "Carbon emissions estimate: 82 kg"],
    ["Above average legroom (33 in)", "In-seat USB outlet", "Stream media to your device", "Carbon emissions estimate: 95 kg"],
    ["Below average legroom (28 in)", "Stream media to your device", "Carbon emissions estimate: 123 kg"],
    ["Carbon emissions estimate: 140 kg"],
    ["Carbon emissions estimate: 95 kg"],
    ["Average legroom (31 in)", "In-seat USB outlet", "On-demand video", "Carbon emissions estimate: 135 kg"],
]

# Hotel data per city
HOTEL_CITIES = [
    # Cities NOT already in dataset (existing = Madiun, Kediri, Blitar, Batu, etc all East Java)
    # We'll add new cities from other provinces
    ("Jakarta", [
        ("Grand Hyatt Jakarta", 5, 2800000, 4.7, 12500, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Plaza Indonesia", "Monas", "Bandar Udara Internasional Soekarno–Hatta"]),
        ("Pullman Jakarta Indonesia", 5, 2200000, 4.6, 8900, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Grand Indonesia", "Monas", "Bandar Udara Internasional Soekarno–Hatta"]),
        ("Novotel Jakarta Gajah Mada", 4, 950000, 4.4, 5200, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Kota Tua Jakarta", "Glodok", "Bandar Udara Internasional Soekarno–Hatta"]),
        ("ibis Jakarta Harmoni", 3, 420000, 4.3, 6800, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning"],
         ["Monas", "Kota Tua Jakarta", "Bandar Udara Internasional Soekarno–Hatta"]),
        ("AONE Hotel Jakarta", 4, 680000, 4.5, 4300, None, None,
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Monas", "Stasiun Gambir", "Bandar Udara Internasional Soekarno–Hatta"]),
    ]),
    ("Surabaya", [
        ("JW Marriott Hotel Surabaya", 5, 2750000, 4.8, 9200, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Tunjungan Plaza", "Monumen Kapal Selam", "Bandar Udara Internasional Juanda"]),
        ("Shangri-La Hotel Surabaya", 5, 2100000, 4.7, 7800, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Tunjungan Plaza", "Kota Tua Surabaya", "Bandar Udara Internasional Juanda"]),
        ("ibis Surabaya City Center", 3, 490000, 4.4, 3800, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Tunjungan Plaza", "Monumen Tugu Pahlawan", "Bandar Udara Internasional Juanda"]),
        ("Novotel Surabaya Hotel", 4, 1120000, 4.5, 4600, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Galaxy Mall", "Kota Tua Surabaya", "Bandar Udara Internasional Juanda"]),
    ]),
    ("Bandung", [
        ("Trans Luxury Hotel Bandung", 5, 2580000, 4.8, 7200, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Trans Studio Bandung", "Paris Van Java", "Bandar Udara Internasional Husein Sastranegara"]),
        ("Padma Hotel Bandung", 5, 2150000, 4.8, 8400, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Lembang", "Tangkuban Perahu", "Bandar Udara Internasional Husein Sastranegara"]),
        ("ibis Bandung Trans Studio", 3, 520000, 4.5, 6800, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Trans Studio Bandung", "Paris Van Java", "Bandar Udara Internasional Husein Sastranegara"]),
        ("Four Points by Sheraton Bandung", 4, 1420000, 4.6, 4800, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Gedung Sate", "Jalan Braga", "Bandar Udara Internasional Husein Sastranegara"]),
        ("Savoy Homann Bidakara Hotel", 4, 980000, 4.4, 3200, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Air conditioning", "Bar"],
         ["Asia Afrika Street", "Gedung Merdeka", "Bandar Udara Internasional Husein Sastranegara"]),
    ]),
    ("Yogyakarta", [
        ("Hotel Tentrem Yogyakarta", 5, 2100000, 4.8, 6300, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Malioboro", "Kraton Yogyakarta", "Bandar Udara Internasional Yogyakarta"]),
        ("Hyatt Regency Yogyakarta", 5, 2850000, 4.7, 8900, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Candi Prambanan", "Malioboro", "Bandar Udara Internasional Yogyakarta"]),
        ("ibis Styles Yogyakarta", 3, 480000, 4.5, 3800, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Malioboro", "Kraton Yogyakarta", "Bandar Udara Internasional Yogyakarta"]),
        ("Alana Yogyakarta Hotel", 4, 890000, 4.4, 2300, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Malioboro", "Taman Sari", "Bandar Udara Internasional Yogyakarta"]),
    ]),
    ("Semarang", [
        ("Ciputra Hotel Semarang", 5, 1380000, 4.7, 4200, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Lawang Sewu", "Simpang Lima", "Bandar Udara Internasional Ahmad Yani"]),
        ("Novotel Semarang", 4, 1050000, 4.5, 5100, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Simpang Lima", "Lawang Sewu", "Bandar Udara Internasional Ahmad Yani"]),
        ("ibis Semarang Simpang Lima", 3, 420000, 4.4, 4600, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Simpang Lima", "Lawang Sewu", "Bandar Udara Internasional Ahmad Yani"]),
        ("Hotel Gumaya Tower", 5, 1200000, 4.5, 2900, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Bar"],
         ["Kota Lama Semarang", "Lawang Sewu", "Bandar Udara Internasional Ahmad Yani"]),
    ]),
    ("Makassar", [
        ("Aryaduta Makassar", 5, 1580000, 4.7, 5100, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Fort Rotterdam", "Pantai Losari", "Bandar Udara Internasional Sultan Hasanuddin"]),
        ("Grand Clarion Hotel Makassar", 4, 980000, 4.5, 4200, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Mall Panakkukang", "Pantai Losari", "Bandar Udara Internasional Sultan Hasanuddin"]),
        ("ibis Makassar City Center", 3, 420000, 4.4, 2900, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Pantai Losari", "Fort Rotterdam", "Bandar Udara Internasional Sultan Hasanuddin"]),
        ("Swiss-Belhotel Makassar", 5, 1320000, 4.6, 3800, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Losari", "Fort Rotterdam", "Bandar Udara Internasional Sultan Hasanuddin"]),
    ]),
    ("Denpasar", [
        ("The Kuta Beach Heritage Hotel Bali", 5, 2100000, 4.7, 6300, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Pantai Kuta", "Pura Tanah Lot", "Bandar Udara Internasional Ngurah Rai"]),
        ("Grand Inna Bali Beach Hotel", 5, 1620000, 4.5, 5800, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Sanur", "Museum Le Mayeur", "Bandar Udara Internasional Ngurah Rai"]),
        ("ibis Bali Legian Street", 3, 550000, 4.4, 5200, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Pantai Legian", "Pantai Kuta", "Bandar Udara Internasional Ngurah Rai"]),
        ("Ramada Bintang Bali Resort", 5, 1450000, 4.5, 4100, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Pantai Kuta", "Discovery Shopping Mall", "Bandar Udara Internasional Ngurah Rai"]),
    ]),
    ("Medan", [
        ("JW Marriott Hotel Medan", 5, 1818624, 4.7, 13182, "15.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Hot tub"],
         ["Rahmat International Wildlife Museum & Gallery", "Kopi Khoo Cafe", "Bandar Udara Internasional Kualanamu"]),
        ("Grand Mercure Maha Cipta Medan Angkasa", 5, 635238, 4.6, 8951, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Tjong A Fie Mansion", "Universitas HKBP Nommensen", "Bandar Udara Internasional Kualanamu"]),
        ("Harper Wahid Hasyim Medan", 3, 666803, 4.8, 5403, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Air conditioning", "Restaurant"],
         ["Merdeka Walk", "Halte Ramayana Pringgan", "Bandar Udara Internasional Kualanamu"]),
        ("ibis Styles Medan Pattimura", 3, 426982, 4.4, 3177, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Indoor pool", "Air conditioning"],
         ["Istana Maimun", "Mongonsidi", "Bandar Udara Internasional Kualanamu"]),
        ("ARYADUTA Medan", 5, 692070, 4.5, 5631, "14.00", "12.00",
         ["Breakfast", "Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Merdeka Walk", "Kantor Walikota", "Bandar Udara Internasional Kualanamu"]),
    ]),
    ("Manado", [
        ("Sintesa Peninsula Hotel Manado", 5, 1650000, 4.7, 3840, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Taman Nasional Bunaken", "Pantai Malalayang", "Bandar Udara Internasional Sam Ratulangi"]),
        ("Novotel Manado Golf Resort", 5, 1850000, 4.7, 3210, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Lapangan Golf Manado", "Pantai Malalayang", "Bandar Udara Internasional Sam Ratulangi"]),
        ("Hotel Gran Puri Manado", 4, 720000, 4.3, 1780, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Spa"],
         ["Sam Ratulangi Museum", "Pantai Malalayang", "Bandar Udara Internasional Sam Ratulangi"]),
    ]),
    ("Balikpapan", [
        ("Gran Senyiur Hotel Balikpapan", 5, 1420000, 4.6, 3210, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Kemala", "Masjid Agung Balikpapan", "Bandar Udara Internasional Sultan Aji Muhammad Sulaiman"]),
        ("Novotel Balikpapan", 4, 1180000, 4.5, 4580, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Manggar", "Balikpapan Plaza", "Bandar Udara Internasional Sultan Aji Muhammad Sulaiman"]),
        ("Aston Balikpapan Hotel", 4, 750000, 4.3, 2120, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Bar"],
         ["Masjid Agung Balikpapan", "Balikpapan Plaza", "Bandar Udara Internasional Sultan Aji Muhammad Sulaiman"]),
    ]),
    ("Pekanbaru", [
        ("Aryaduta Pekanbaru", 5, 1580000, 4.7, 4210, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Masjid Raya Annur", "Pasar Bawah", "Bandar Udara Internasional Sultan Syarif Kasim II"]),
        ("Grand Zuri Hotel Pekanbaru", 4, 980000, 4.6, 3840, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Masjid Raya Annur", "Taman Rekreasi Alam Mayang", "Bandar Udara Internasional Sultan Syarif Kasim II"]),
        ("ibis Pekanbaru Hotel", 3, 450000, 4.4, 3120, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Masjid Raya Annur", "Pasar Bawah", "Bandar Udara Internasional Sultan Syarif Kasim II"]),
    ]),
    ("Lombok", [
        ("The Oberoi Beach Resort Lombok", 5, 4200000, 4.9, 3120, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Pantai Senggigi", "Gili Trawangan", "Bandar Udara Internasional Lombok"]),
        ("Sheraton Lombok Resort", 5, 3100000, 4.7, 4580, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Mandalika", "Sirkuit Mandalika", "Bandar Udara Internasional Lombok"]),
        ("Novotel Lombok Resort", 4, 1850000, 4.6, 5830, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Pantai Senggigi", "Gunung Rinjani", "Bandar Udara Internasional Lombok"]),
        ("Qunci Villas Hotel", 4, 980000, 4.7, 2140, "13.00", "11.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Pantai Senggigi", "Gunung Rinjani", "Bandar Udara Internasional Lombok"]),
    ]),
    ("Labuan Bajo", [
        ("Ayana Komodo Waecicu Beach", 5, 5800000, 4.9, 2410, "15.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Pulau Komodo", "Pantai Pink", "Bandar Udara Internasional Komodo"]),
        ("Plataran Komodo Resort", 5, 4200000, 4.8, 1840, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Taman Nasional Komodo", "Pulau Rinca", "Bandar Udara Internasional Komodo"]),
        ("Hotel Bintang Flores", 4, 1200000, 4.5, 3120, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Pelabuhan Labuan Bajo", "Pulau Komodo", "Bandar Udara Internasional Komodo"]),
    ]),
    ("Ambon", [
        ("Swiss-Belhotel Ambon", 4, 980000, 4.5, 2130, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Pantai Natsepa", "Gong Perdamaian Dunia", "Bandar Udara Internasional Pattimura"]),
        ("Aston Natsepa Resort", 4, 850000, 4.5, 3120, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning", "Bar"],
         ["Pantai Natsepa", "Museum Siwalima", "Bandar Udara Internasional Pattimura"]),
        ("Manise Hotel Ambon", 4, 680000, 4.4, 1580, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Gym"],
         ["Museum Siwalima", "Pantai Natsepa", "Bandar Udara Internasional Pattimura"]),
    ]),
    ("Solo", [
        ("The Sunan Hotel Solo", 5, 1580000, 4.7, 5120, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning", "Spa"],
         ["Keraton Surakarta", "Pasar Klewer", "Bandar Udara Internasional Adi Soemarmo"]),
        ("Grand Mercure Solo Baru", 5, 1350000, 4.6, 4210, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Solo Square", "Keraton Surakarta", "Bandar Udara Internasional Adi Soemarmo"]),
        ("ibis Solo", 3, 480000, 4.4, 4580, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Air conditioning", "Fitness center"],
         ["Jalan Slamet Riyadi", "Pasar Klewer", "Bandar Udara Internasional Adi Soemarmo"]),
        ("Novotel Solo", 4, 1050000, 4.5, 5840, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Jalan Slamet Riyadi", "Pasar Klewer", "Bandar Udara Internasional Adi Soemarmo"]),
    ]),
    ("Palembang", [
        ("Hotel Aryaduta Palembang", 5, 1250000, 4.6, 3120, "14.00", "12.00",
         ["Free breakfast", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Jembatan Ampera", "Museum Sultan Mahmud Badaruddin II", "Bandar Udara Internasional Sultan Mahmud Badaruddin II"]),
        ("Novotel Palembang", 4, 980000, 4.5, 4210, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"],
         ["Jembatan Ampera", "Benteng Kuto Besak", "Bandar Udara Internasional Sultan Mahmud Badaruddin II"]),
        ("Aston Palembang Hotel", 4, 750000, 4.4, 2840, "14.00", "12.00",
         ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"],
         ["Palem Grand Mall", "Jembatan Ampera", "Bandar Udara Internasional Sultan Mahmud Badaruddin II"]),
    ]),
]

HOTEL_USER_QUERIES = [
    "Cari Hotel di {}",
    "Cari hotel di {}",
    "Carikan hotel di {}",
    "Info hotel di {}",
    "Hotel di {} dong",
    "Rekomendasi hotel di {}",
    "Saya mau cari hotel di {}",
    "Ada hotel di {} gak?",
    "Tolong carikan hotel di {}",
    "Hotel apa yang bagus di {}?",
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fmt_price(p):
    return f"{int(p):,}".replace(",", ".")

def kmh_to_knots(kmh):
    return round(kmh / 1.852, 1)

def rand_date(start_year=2026, start_month=6):
    start = date(start_year, start_month, 1)
    end = date(2027, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d

def fmt_date(d):
    return d.strftime("%Y-%m-%d")

def interpret_ext(ext):
    if ext.startswith("Below average legroom"):
        return "Ruang kaki sempit"
    elif ext.startswith("Above average legroom"):
        return "Ruang kaki luas"
    elif ext.startswith("Average legroom"):
        return "Ruang kaki standar"
    elif ext.startswith("Carbon emissions estimate"):
        val = ext.split(":")[-1].strip()
        return f"Estimasi emisi karbon: {val}"
    elif ext.startswith("On-demand video"):
        return "Hiburan di pesawat tersedia"
    elif ext.startswith("In-seat USB outlet"):
        return "Colokan USB tersedia"
    elif ext.startswith("Stream media to your device"):
        return "Streaming media ke perangkat"
    return ext

def interpret_amenity(a):
    if "($)" in a:
        a = a.replace("($)", "").strip()
        replacements = {"Breakfast": "Sarapan", "Parking": "Parkir", "Pool": "Kolam renang"}
        for eng, ind in replacements.items():
            if eng in a:
                a = a.replace(eng, ind)
        return f"{a} (berbayar)"
    return a

def get_pakaian(temp, weather):
    wl = weather.lower()
    if temp <= 20:
        return "Pakaian hangat atau jaket tebal sangat disarankan karena suhu cukup dingin"
    elif temp <= 23:
        if "hujan" in wl:
            return "Pakaian ringan berlapis dengan jaket tahan air, hindari bahan yang mudah basah"
        return "Pakaian ringan berlapis seperti kemeja panjang atau jaket tipis cukup nyaman"
    elif temp <= 26:
        if "hujan" in wl:
            return "Pakaian ringan berbahan cepat kering, bawa jaket tipis atau jas hujan"
        elif "cerah" in wl and "berawan" not in wl:
            return "Pakaian ringan dan breathable seperti kaos katun atau linen sangat nyaman"
        return "Pakaian ringan dan nyaman, bisa tambahkan jaket tipis jika perlu"
    else:
        if "hujan" in wl:
            return "Pakaian ringan berbahan cepat kering, siapkan jas hujan atau payung"
        return "Pakaian ringan dan breathable, hindari warna gelap agar tidak terlalu panas"

def get_perlengkapan(weather, visibility):
    wl = weather.lower()
    items = []
    if "hujan lebat" in wl or "petir" in wl:
        items += ["jas hujan atau payung besar", "sepatu anti air", "tas waterproof"]
    elif "hujan" in wl:
        items += ["payung atau jas hujan", "sandal atau sepatu anti air"]
    elif "cerah" in wl and "berawan" not in wl:
        items += ["sunscreen SPF 30+", "kacamata hitam", "topi atau pelindung kepala"]
    elif "kabut" in wl or "asap" in wl:
        items += ["masker untuk melindungi dari polutan", "kacamata jika berkendara"]
    else:
        items.append("payung lipat antisipasi perubahan cuaca")
    if visibility and "< 10" in str(visibility):
        items.append("waspada visibilitas rendah saat berkendara")
    return ", ".join(items) if items else "payung lipat sebagai antisipasi"

# ============================================================
# GENERATORS
# ============================================================

def make_bmkg_ok(city):
    adm4 = ADM4_MAP.get(city, "00.00.00.0000")
    temp = random.randint(18, 35)
    humidity = random.randint(55, 98)
    wind_kmh = round(random.uniform(0.5, 35.0), 1)
    wind_knots = kmh_to_knots(wind_kmh)
    visibility_options = ["< 10 km", "> 10 km", "5-10 km"]
    visibility = random.choice(visibility_options)
    weather = random.choice(WEATHER_STATUSES)

    query = random.choice(BMKG_QUERIES).format(city)

    analysis_date = "2026-" + f"{random.randint(1,12):02d}-{random.randint(1,28):02d}" + "T12:00:00"
    local_datetime = "2026-" + f"{random.randint(1,12):02d}-{random.randint(1,28):02d}" + f" {random.randint(0,23):02d}:00:00"

    tool_result = {
        "status": "OK",
        "data": {
            "location_name": city,
            "adm4": adm4,
            "weather": {
                "source": "BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)",
                "location_code": adm4,
                "analysis_date": analysis_date,
                "local_datetime": local_datetime,
                "temperature_c": temp,
                "humidity_percent": humidity,
                "weather": weather,
                "wind_speed_kmh": wind_kmh,
                "visibility": visibility
            },
            "params": {"query": query}
        }
    }

    system_content = BMKG_SYSTEM_PREFIX + json.dumps(tool_result, ensure_ascii=False)
    pakaian = get_pakaian(temp, weather)
    perlengkapan = get_perlengkapan(weather, visibility)

    assistant_content = (
        f"Halo! Selamat datang di layanan prakiraan cuaca BMKG untuk **{city}**. Berikut kondisi cuaca terkini:\n\n"
        f"Kondisi Cuaca Terkini:\n"
        f"- **Status Cuaca**: {weather}\n"
        f"- **Suhu Udara**: {temp}°C\n"
        f"- **Kelembaban**: {humidity}%\n"
        f"- **Kecepatan Angin**: {wind_knots} knots\n"
        f"- **Visibilitas**: {visibility}\n\n"
        f"Rekomendasi Praktis Wisatawan:\n"
        f"- **Pakaian yang Cocok**: {pakaian}\n"
        f"- **Perlengkapan Wajib**: {perlengkapan}\n\n"
        f"Semoga aktivitas Anda di **{city}** menyenangkan dan tetap aman! 🌤️"
    )

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
            {"role": "assistant", "content": assistant_content}
        ]
    }

def make_bmkg_not_found(city):
    query = random.choice(BMKG_QUERIES).format(city)
    tool_result = {
        "status": "NOT_FOUND",
        "error": "Location not found in BMKG database",
        "data": {"params": {"query": query}}
    }
    system_content = BMKG_SYSTEM_PREFIX + json.dumps(tool_result, ensure_ascii=False)
    assistant_content = (
        f"Hai! Maaf, informasi cuaca untuk **{city}** belum tersedia dalam sistem BMKG kami. "
        f"Lokasi tersebut mungkin menggunakan nama berbeda atau belum tercakup dalam database.\n\n"
        f"Silakan coba:\n"
        f"- Periksa ejaan nama kota atau kabupaten\n"
        f"- Gunakan nama kota/kabupaten yang lebih umum\n"
        f"- Coba nama kecamatan atau daerah terdekat yang lebih besar"
    )
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
            {"role": "assistant", "content": assistant_content}
        ]
    }

def make_bmkg_ambiguous(city, candidates):
    query = random.choice(BMKG_QUERIES).format(city)
    tool_result = {
        "status": "AMBIGUOUS",
        "data": {
            "field": "location",
            "candidates": candidates,
            "params": {"query": query}
        }
    }
    system_content = BMKG_SYSTEM_PREFIX + json.dumps(tool_result, ensure_ascii=False)
    cand_list = "\n".join([f"- {c}" for c in candidates])
    assistant_content = (
        f"Hai! Nama **{city}** yang Anda masukkan ditemukan di beberapa lokasi berbeda. "
        f"Mohon perjelas lokasi yang dimaksud:\n\n"
        f"{cand_list}\n\n"
        f"Silakan sebutkan nama lengkap atau nama kabupaten/kotanya agar saya bisa memberikan informasi cuaca yang tepat!"
    )
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
            {"role": "assistant", "content": assistant_content}
        ]
    }

def make_flight(route):
    dep_id, arr_id, dep_city, arr_city, duration = route
    dep_date = rand_date()
    nights = random.randint(0, 14)
    arr_date = dep_date + timedelta(days=nights)

    num_flights = random.randint(2, 6)
    selected_airlines = random.sample(AIRLINES, min(num_flights, len(AIRLINES)))

    flights = []
    for i, (airline_name, code, planes) in enumerate(selected_airlines):
        plane = random.choice(planes)
        hour = random.randint(5, 21)
        minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
        dep_time = f"{fmt_date(dep_date)} {hour:02d}:{minute:02d}"
        arr_dt = dep_date if duration < 60 else dep_date
        arr_hour = (hour * 60 + minute + duration) // 60 % 24
        arr_min = (hour * 60 + minute + duration) % 60
        arr_time = f"{fmt_date(dep_date)} {arr_hour:02d}:{arr_min:02d}"

        exts = random.choice(EXTENSIONS_POOL)
        price = random.choice([None, None, random.randint(500000, 5000000)])
        fn_num = random.randint(100, 999)
        flight_number = f"{code} {fn_num}"

        flights.append({
            "type": None,
            "airplane": plane,
            "airline": airline_name,
            "travel_class": "Economy",
            "legroom": None,
            "extensions": exts,
            "flight_number": flight_number,
            "departure": dep_time,
            "arrival": arr_time,
            "duration_minutes": duration,
            "price_idr": price,
            "departure_airport_name": f"{dep_city} Airport",
            "departure_airport_id": dep_id,
            "departure_time": dep_time,
            "arrival_airport_name": f"{arr_city} Airport",
            "arrival_airport_id": arr_id,
            "arrival_time": arr_time,
            "departure_date": fmt_date(dep_date),
            "return_date": fmt_date(arr_date)
        })

    tool_result = {
        "search": {
            "departure_date": fmt_date(dep_date),
            "arrival_date": fmt_date(arr_date)
        },
        "flights": flights
    }

    system_content = FLIGHT_SYSTEM_PREFIX + json.dumps(tool_result, ensure_ascii=False)

    user_queries = [
        f"Cari tiket ke {arr_city}",
        f"Cari tiket dari {dep_city} ke {arr_city}",
        f"Penerbangan ke {arr_city} dong",
        f"Ada tiket {dep_city} - {arr_city} gak?",
        f"Mau terbang ke {arr_city} dari {dep_city}",
        f"Info penerbangan {dep_id} ke {arr_id}",
        f"Tiket pesawat ke {arr_city}",
    ]
    user_msg = random.choice(user_queries)

    # Build assistant response
    lines = [
        f"Pesawat yang tersedia dari Bandara {dep_id} ke Bandara {arr_id} pada tanggal "
        f"{fmt_date(dep_date)} - {fmt_date(arr_date)} terdapat {len(flights)} penerbangan:"
    ]
    for f in flights:
        dep_hm = f["departure_time"][11:16]
        arr_hm = f["arrival_time"][11:16]
        price_str = f"Rp {fmt_price(f['price_idr'])}" if f["price_idr"] else "Rp -"
        ext_list = [interpret_ext(e) for e in f["extensions"]]
        ext_str = ", ".join(ext_list) if ext_list else "Informasi tambahan tidak tersedia"
        lines.append(
            f"- **{f['airline']} ({f['flight_number']})**\n"
            f"  Jam: {dep_hm} - {arr_hm}\n"
            f"  Kelas: {f['travel_class']}\n"
            f"  Harga: {price_str}\n"
            f"  Detail: Menggunakan pesawat {f['airplane']}, {ext_str}"
        )

    assistant_content = "\n".join(lines)

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_content}
        ]
    }

def make_hotel(city, hotels_data, check_in=None, check_out=None):
    if check_in is None:
        ci = rand_date()
        nights = random.randint(1, 7)
        co = ci + timedelta(days=nights)
    else:
        ci, co = check_in, check_out
        nights = (co - ci).days

    # Pick 2-6 hotels randomly from pool
    num = random.randint(2, min(len(hotels_data), 6))
    selected = random.sample(hotels_data, num)

    hotels = []
    for h in selected:
        name, hclass, price_per_night, rating, reviews, checkin_t, checkout_t, amenities, nearby = h
        total = price_per_night * nights
        hotels.append({
            "name": name,
            "hotel_class": hclass,
            "price_per_night": price_per_night,
            "total_price": total,
            "rating": rating,
            "reviews": reviews,
            "location_rating": round(random.uniform(3.5, 5.0), 1),
            "amenities": amenities,
            "check_in": checkin_t,
            "check_out": checkout_t,
            "nearby": nearby,
            "property_token": f"ChcI{random.randint(10000,99999)}"
        })

    tool_result = {
        "search": {
            "check_in_date": fmt_date(ci),
            "check_out_date": fmt_date(co)
        },
        "hotels": hotels
    }

    system_content = HOTEL_SYSTEM_PREFIX + json.dumps(tool_result, ensure_ascii=False)
    user_msg = random.choice(HOTEL_USER_QUERIES).format(city)

    # Build assistant response
    lines = [
        f"Berikut adalah beberapa rekomendasi hotel di {city} untuk masa inap "
        f"{fmt_date(ci)} - {fmt_date(co)} ({nights} malam)",
        f"Hotel yang tersedia ada {len(hotels)}:",
        ""
    ]
    for h in hotels:
        rating_str = str(round(h["rating"], 2)) if h["rating"] else "Belum ada rating"
        reviews_str = str(h["reviews"]) if h["reviews"] else "0"
        checkin_str = h["check_in"] if h["check_in"] else "Belum ada waktu"
        checkout_str = h["check_out"] if h["check_out"] else "Belum ada waktu"
        amenities_str = ", ".join([interpret_amenity(a) for a in h["amenities"]])
        nearby_str = ", ".join(h["nearby"]) if h["nearby"] else "(Tidak ada informasi)"

        lines += [
            f"- **{h['name']}**",
            f"  Rating: {rating_str} ({reviews_str} ulasan)",
            f"  Estimasi Harga per Malam: Rp {fmt_price(h['price_per_night'])}",
            f"  Total Harga: Rp {fmt_price(h['total_price'])}",
            f"  Waktu Check-In: {checkin_str}",
            f"  Waktu Check-Out: {checkout_str}",
            f"  Fasilitas: {amenities_str}",
            f"  Tempat Terdekat: {nearby_str}",
            ""
        ]

    assistant_content = "\n".join(lines).strip()

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_content}
        ]
    }

# ============================================================
# GENERATE
# ============================================================

random.seed(42)
new_records = []

# --- BMKG: target 200 new records ---
print("Generating BMKG records...")
bmkg_count = 0

# OK status - new cities
city_pool = NEW_BMKG_CITIES.copy()
random.shuffle(city_pool)
for city in city_pool:
    # 2-3 records per city with different weather/time
    for _ in range(random.randint(2, 3)):
        new_records.append(make_bmkg_ok(city))
        bmkg_count += 1
        if bmkg_count >= 140:
            break
    if bmkg_count >= 140:
        break

# Also add more variations for existing cities (different weather conditions)
existing_list = list(EXISTING_BMKG)
random.shuffle(existing_list)
for city in existing_list:
    new_records.append(make_bmkg_ok(city))
    bmkg_count += 1
    if bmkg_count >= 190:
        break

# NOT_FOUND
for city in random.sample(NOT_FOUND_CITIES, min(len(NOT_FOUND_CITIES), 10)):
    new_records.append(make_bmkg_not_found(city))
    bmkg_count += 1

# AMBIGUOUS
for city, candidates in list(AMBIGUOUS_CITIES.items())[:10]:
    new_records.append(make_bmkg_ambiguous(city, candidates))
    bmkg_count += 1

print(f"  Generated {bmkg_count} BMKG records")

# --- FLIGHT: target 200 new records ---
print("Generating Flight records...")
flight_count = 0
route_pool = ROUTES.copy()
while flight_count < 200:
    route = random.choice(route_pool)
    new_records.append(make_flight(route))
    flight_count += 1
print(f"  Generated {flight_count} Flight records")

# --- HOTEL: target 200 new records ---
print("Generating Hotel records...")
hotel_count = 0
city_hotel_pool = HOTEL_CITIES.copy()
while hotel_count < 200:
    city, hotels_data = random.choice(city_hotel_pool)
    new_records.append(make_hotel(city, hotels_data))
    hotel_count += 1
print(f"  Generated {hotel_count} Hotel records")

# Shuffle all new records
random.shuffle(new_records)

print(f"\nTotal new records: {len(new_records)}")

# Save new records only
out_new = "data/full/new_records_bmkg_flight_hotel.jsonl"
with open(out_new, "w", encoding="utf-8") as f:
    for r in new_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"Saved new records to: {out_new}")

# Merge with existing fixed dataset
with open("data/full/full_dataset_copy.jsonl", encoding="utf-8") as f:
    existing = f.readlines()

merged_path = "data/full/full_dataset_augmented.jsonl"
with open(merged_path, "w", encoding="utf-8") as f:
    for line in existing:
        f.write(line if line.endswith("\n") else line + "\n")
    for r in new_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Saved merged dataset to: {merged_path}")
print(f"Total merged: {len(existing) + len(new_records)} records")