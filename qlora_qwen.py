# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
# from peft import PeftModel

# base_model_name = "Qwen/Qwen2-7B-Instruct"
# adapter_path = "./qwen-toba-final"

# # Load tokenizer
# tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
# tokenizer.pad_token = tokenizer.eos_token

# # Load base model
# base_model = AutoModelForCausalLM.from_pretrained(
#     base_model_name,
#     torch_dtype=torch.float16,
#     device_map="auto",
#     trust_remote_code=True
# )

# # Load adapter
# model = PeftModel.from_pretrained(base_model, adapter_path)

# # Test inference
# messages = [
#     {"role": "system", "content": "You are a travel assistant."},
#     {"role": "user", "content": "Buat itinerary 2 hari di Danau Toba"}
# ]

# input_text = tokenizer.apply_chat_template(messages, tokenize=False)
# inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

# outputs = model.generate(**inputs, max_new_tokens=200)
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))

import torch
import json
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# =========================
# CONFIG
# =========================
base_model_name = "Qwen/Qwen2-7B-Instruct"
adapter_path = "./qwen2-7b-instruct-finetuned-final"
output_file = f"inference_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

FLIGHT_PROMPT = """Kamu adalah AI Ekstraktor Data Penerbangan. Tugasmu adalah menampilkan SEMUA opsi penerbangan dari TOOL_RESULT secara lengkap dan terstruktur. Jangan merangkum atau melewatkan data.

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
  - "Carbon emissions estimate" → "Estimasi emisi karbon"
  - "On-demand video" → "Hiburan di pesawat tersedia"
- Jika extensions kosong → "Informasi tambahan tidak tersedia"
- Jangan mengubah nilai data
- Tampilkan semua penerbangan tanpa terlewat
- Jangan menambahkan penomoran seperti "1.", "2.", dst.
- Gunakan format bullet "-" sesuai instruksi.
- Header harus ditulis PERSIS seperti format:
  "Pesawat yang tersedia dari Bandara [departure_airport_id] ke Bandara [arrival_airport_id] ada [jumlah penerbangan]:"
  (Jangan menambahkan kata seperti "penerbangan" di akhir)
- Jangan menambahkan teks di luar format yang diminta.

====================
TOOL_RESULT:
{"search": {"departure_date": "2026-09-10", "arrival_date": "2026-09-15"}, "flights": [{"type": null, "airplane": "Boeing 737", "airline": "Lion", "travel_class": "Economy", "legroom": "29 in", "extensions": ["Below average legroom (29 in)", "Carbon emissions estimate: 88 kg"], "flight_number": "JT 30", "departure": "2026-09-10 08:20", "arrival": "2026-09-10 11:15", "duration_minutes": 115, "price_idr": 3312300, "departure_airport_name": "Soekarno–Hatta International Airport", "departure_airport_id": "CGK", "departure_time": "2026-09-10 08:20", "arrival_airport_name": "I Gusti Ngurah Rai International Airport", "arrival_airport_id": "DPS", "arrival_time": "2026-09-10 11:15", "departure_date": "2026-09-10", "return_date": "2026-09-15"}, {"type": null, "airplane": "Airbus A320", "airline": "Indonesia AirAsia", "travel_class": "Economy", "legroom": "28 in", "extensions": ["Below average legroom (28 in)", "Carbon emissions estimate: 96 kg"], "flight_number": "QZ 802", "departure": "2026-09-10 09:45", "arrival": "2026-09-10 12:35", "duration_minutes": 110, "price_idr": 3414741, "departure_airport_name": "Soekarno–Hatta International Airport", "departure_airport_id": "CGK", "departure_time": "2026-09-10 09:45", "arrival_airport_name": "I Gusti Ngurah Rai International Airport", "arrival_airport_id": "DPS", "arrival_time": "2026-09-10 12:35", "departure_date": "2026-09-10", "return_date": "2026-09-15"}, {"type": null, "airplane": "Boeing 737", "airline": "Garuda Indonesia", "travel_class": "Economy", "legroom": "31 in", "extensions": ["Average legroom (31 in)", "On-demand video", "Carbon emissions estimate: 107 kg"], "flight_number": "GA 404", "departure": "2026-09-10 09:30", "arrival": "2026-09-10 12:25", "duration_minutes": 115, "price_idr": 4155511, "departure_airport_name": "Soekarno–Hatta International Airport", "departure_airport_id": "CGK", "departure_time": "2026-09-10 09:30", "arrival_airport_name": "I Gusti Ngurah Rai International Airport", "arrival_airport_id": "DPS", "arrival_time": "2026-09-10 12:25", "departure_date": "2026-09-10", "return_date": "2026-09-15"}, {"type": null, "airplane": "Boeing 737", "airline": "Nam Air", "travel_class": "Economy", "legroom": null, "extensions": ["Carbon emissions estimate: 140 kg"], "flight_number": "IN 282", "departure": "2026-09-10 05:30", "arrival": "2026-09-10 08:20", "duration_minutes": 110, "price_idr": null, "departure_airport_name": "Soekarno–Hatta International Airport", "departure_airport_id": "CGK", "departure_time": "2026-09-10 05:30", "arrival_airport_name": "I Gusti Ngurah Rai International Airport", "arrival_airport_id": "DPS", "arrival_time": "2026-09-10 08:20", "departure_date": "2026-09-10", "return_date": "2026-09-15"}, {"type": null, "airplane": "Boeing 737", "airline": "Sriwijaya Air", "travel_class": "Economy", "legroom": null, "extensions": ["Carbon emissions estimate: 95 kg"], "flight_number": "SJ 272", "departure": "2026-09-10 18:00", "arrival": "2026-09-10 20:50", "duration_minutes": 110, "price_idr": null, "departure_airport_name": "Soekarno–Hatta International Airport", "departure_airport_id": "CGK", "departure_time": "2026-09-10 18:00", "arrival_airport_name": "I Gusti Ngurah Rai International Airport", "arrival_airport_id": "DPS", "arrival_time": "2026-09-10 20:50", "departure_date": "2026-09-10", "return_date": "2026-09-15"}]}"""

SYSTEM_PROMPT = """
Kamu adalah AI Travel Planner Eksklusif untuk 5 Destinasi Super Prioritas Indonesia (Labuan Bajo, Borobudur, Mandalika, Danau Toba, dan Likupang).

====================
ATURAN KETAT (WAJIB DIPATUHI)
====================
1. PILIH SATU SAJA: Jika User meminta rekomendasi umum, JANGAN merangkum ke-5 destinasi. PILIH HANYA SATU destinasi untuk dibahas secara sangat mendalam.
2. FAKTA AKURAT (ANTI-HALUSINASI): Gunakan data dunia nyata! (Contoh: Labuan Bajo adalah habitat Komodo, BUKAN dinosaurus).
3. PANJANG JAWABAN: Jawaban WAJIB panjang dan detail (minimal 400 kata). Jangan pernah menjawab dengan poin-poin singkat!
4. GAYA BAHASA: Sangat deskriptif, profesional, dan menginspirasi.

====================
STRUKTUR OUTPUT (WAJIB GUNAKAN FORMAT INI)
====================
Kamu harus membagi jawaban ke dalam 4 paragraf panjang dengan urutan ini:

PEMBUKA:
(Tulis 1 paragraf panjang berisi pengantar yang sangat menarik tentang daya tarik destinasi yang kamu pilih)

REKOMENDASI AKTIVITAS:
(Tulis 1 paragraf panjang dan detail yang menyebutkan minimal 3 lokasi wisata spesifik di destinasi tersebut beserta kegiatan seru dan kekayaan budayanya)

TIPS PERJALANAN:
(Tulis 1 paragraf panjang yang berisi nama bandara terdekat, cara menuju ke sana, dan saran waktu terbaik untuk berkunjung)

PENUTUP:
(Tulis 1 paragraf panjang yang menyimpulkan keindahan destinasi tersebut dan diakhiri dengan kalimat yang sangat antusias mengajak User berlibur di Indonesia untuk menjelajahi pesona nusantara!)
"""

HOTEL_PROMPT = """
Kamu adalah AI Travel Planner yang menampilkan rekomendasi hotel berdasarkan TOOL_RESULT.

====================
FORMAT OUTPUT (WAJIB)
====================

1. Pembuka:
- Jika tersedia check_in_date & check_out_date:
  "Berikut adalah beberapa rekomendasi hotel di Medan untuk masa inap [check_in_date] - [check_out_date] ([jumlah_malam] malam)"
- Jika tidak tersedia:
  "Berikut adalah beberapa rekomendasi hotel di Medan"

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

====================
TOOL_RESULT:
{"search": {"check_in_date": "2026-09-10", "check_out_date": "2026-09-15"}, "hotels": [{"name": "Swiss-Belinn Medan", "hotel_class": 3, "price_per_night": 534400, "total_price": 2672000, "rating": 4.5, "reviews": 8578, "location_rating": 4.5, "amenities": ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Air conditioning", "Fitness center"], "check_in": null, "check_out": null, "nearby": ["Tjong A Fie Mansion", "Jalan Cirebon", "Bandar Udara Internasional Kualanamu"], "property_token": "ChcI57CJlcTJgKFRGgsvZy8xdGRxd3Z0bBAB"}, {"name": "ARYADUTA Medan", "hotel_class": 5, "price_per_night": 692070, "total_price": 3460352, "rating": 4.5, "reviews": 5631, "location_rating": 4.3, "amenities": ["Breakfast", "Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"], "check_in": "14.00", "check_out": "12.00", "nearby": ["Merdeka Walk", "Kantor Walikota", "Bandar Udara Internasional Kualanamu"], "property_token": "ChcImIWZpejI8r06GgsvZy8xdHJyeTQ3dxAB"}, {"name": "Grand Mercure Maha Cipta Medan Angkasa", "hotel_class": 5, "price_per_night": 635238, "total_price": 3176192, "rating": 4.6, "reviews": 8951, "location_rating": 3.5, "amenities": ["Free breakfast", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"], "check_in": "14.00", "check_out": "12.00", "nearby": ["Tjong A Fie Mansion", "Universitas HKBP Nommensen", "Bandar Udara Internasional Kualanamu"], "property_token": "ChcIzoSUvtmtqKlLGgsvZy8xd3ljNm5kZhAB"}, {"name": "AIHO Hotel Medan", "hotel_class": 4, "price_per_night": 495104, "total_price": 2475520, "rating": 4.7, "reviews": 7658, "location_rating": 4.3, "amenities": ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Air conditioning"], "check_in": "15.00", "check_out": "12.00", "nearby": ["Rahmat International Wildlife Museum & Gallery", "Pizza Hut Adam Malik", "Bandar Udara Internasional Kualanamu"], "property_token": "ChkImOP6y9Dzs7gLGg0vZy8xMXFfbXpsN3BiEAE"}, {"name": "ibis Styles Medan Pattimura", "hotel_class": 3, "price_per_night": 426982, "total_price": 2134912, "rating": 4.4, "reviews": 3177, "location_rating": 4.4, "amenities": ["Free breakfast", "Free Wi-Fi", "Free parking", "Indoor pool", "Air conditioning"], "check_in": "14.00", "check_out": "12.00", "nearby": ["Istana Maimun", "Mongonsidi", "Bandar Udara Internasional Kualanamu"], "property_token": "ChoIuurOtuG8kIXBARoNL2cvMTFmMXoxOWRrYxAB"}, {"name": "Harper Wahid Hasyim Medan", "hotel_class": 3, "price_per_night": 666803, "total_price": 3334016, "rating": 4.8, "reviews": 5403, "location_rating": 4.3, "amenities": ["Free breakfast", "Free Wi-Fi", "Free parking", "Air conditioning", "Restaurant"], "check_in": "14.00", "check_out": "12.00", "nearby": ["Merdeka Walk", "Halte Ramayana Pringgan", "Bandar Udara Internasional Kualanamu"], "property_token": "ChkIlcDYjbaTlKQSGg0vZy8xMWg1X3QxaDdtEAE"}, {"name": "NEW DETONGA HOTEL", "hotel_class": 3, "price_per_night": 193978, "total_price": 969888, "rating": 3.3, "reviews": 567, "location_rating": 4.0, "amenities": ["Free breakfast", "Free Wi-Fi", "Free parking", "Pools", "Air conditioning"], "check_in": null, "check_out": null, "nearby": ["Rahmat International Wildlife Museum & Gallery", "Simpang Sei Serayu - Darussalam", "Bandar Udara Internasional Kualanamu"], "property_token": "ChkI18mngPKdydYdGg0vZy8xMW03bjZyaHpwEAE"}, {"name": "Four Points by Sheraton Medan", "hotel_class": 4, "price_per_night": 868454, "total_price": 4342272, "rating": 4.5, "reviews": 5921, "location_rating": 3.9, "amenities": ["Breakfast ($)", "Free Wi-Fi", "Parking ($)", "Outdoor pool", "Air conditioning"], "check_in": "15.00", "check_out": "12.00", "nearby": ["RS Advent", "Bandar Udara Internasional Kualanamu", "Restoran Koki Sunda"], "property_token": "ChgIn67C08vpyoxmGgwvZy8xMmhtZHY4bXYQAQ"}, {"name": "CBD Studio3 next to Sun Plaza Real City Center! - One-Bedroom Apartment", "hotel_class": null, "price_per_night": 899283, "total_price": 4496413, "rating": null, "reviews": null, "location_rating": 4.4, "amenities": ["Ber-AC", "Ranjang bayi", "Gym", "Papan setrika", "Dapur"], "check_in": "14.00", "check_out": "12.00", "nearby": ["Baldish Sport Dan Musik", "Bandar Udara Internasional Kualanamu", "Cahaya Baru"], "property_token": "ChoQ8Lr_zb-R6smhARoNL2cvMTF4ZnB2a2J0NhAC"}, {"name": "JW Marriott Hotel Medan", "hotel_class": 5, "price_per_night": 1818624, "total_price": 9093120, "rating": 4.7, "reviews": 13182, "location_rating": 4.4, "amenities": ["Breakfast ($)", "Free Wi-Fi", "Free parking", "Outdoor pool", "Hot tub"], "check_in": "15.00", "check_out": "12.00", "nearby": ["Rahmat International Wildlife Museum & Gallery", "Kopi Khoo Cafe", "Bandar Udara Internasional Kualanamu"], "property_token": "ChcI_sO0u-eBx7tUGgsvZy8xdGZkdzhsaBAB"}]}
"""

BMKG_PROMPT = """ 
Kamu adalah AI Prakiraan Cuaca Indonesia. Tugasmu adalah menyampaikan kondisi cuaca dari TOOL_RESULT kepada pengguna secara ramah, informatif, dan praktis. 

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
{
  "status": "OK",
  "data": {
    "location_name": "Surakarta",
    "adm4": "33.72.01.1001",
    "weather": {
      "source": "BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)",
      "location_code": "33.72.01.1001",
      "analysis_date": "2026-05-24T12:00:00",
      "local_datetime": "2026-05-25 00:00:00",
      "temperature_c": 24,
      "humidity_percent": 95,
      "weather": "Cerah",
      "wind_speed_kmh": 5.9,
      "visibility": "> 10 km"
    },
    "params": {
      "query": "Apakah hujan di Jakarta?"
    }
  }
}
"""

GENERAL_PROMPT = """


"""

# =========================
# PERTANYAAN TEST
# =========================
test_questions = [
    "Apa keunikan dari Danau Toba?",
]

# =========================
# LOAD MODEL
# =========================
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.bfloat16,   # bfloat16 lebih stabil dari float16
    device_map="auto",
    trust_remote_code=True
)

print("Loading adapter...")
model = PeftModel.from_pretrained(base_model, adapter_path)
model.eval()
print("Model ready!\n")

# =========================
# INFERENCE FUNCTION          # ganti disini prompt
# =========================
def generate_response(question, system_prompt=SYSTEM_PROMPT):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True  # penting untuk inference
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=9000,
            # temperature=0.7,
            do_sample=True,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Ambil hanya bagian response, bukan prompt
    response_ids = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(response_ids, skip_special_tokens=True)
    return response.strip()

# =========================
# RUN & COLLECT RESULTS
# =========================
results = []

for i, question in enumerate(test_questions, 1):
    print(f"[{i}/{len(test_questions)}] Q: {question}")
    response = generate_response(question)
    print(f"A: {response}\n{'-'*60}")

    results.append({
        "id": i,
        "question": question,
        "answer": response,
    })

# =========================
# SAVE TO JSON
# =========================
output = {
    "model": adapter_path,
    "base_model": base_model_name,
    "timestamp": datetime.now().isoformat(),
    "total_questions": len(results),
    "results": results
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved to {output_file}")