import torch
import json
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM

# =========================
# CONFIG
# =========================
model_path = "./qwen-toba-merged"  # ganti sesuai path merge kamu
output_file = f"inference_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

SYSTEM_PROMPT = "You are an accurate and reliable travel information assistant, specializing in Indonesia's five super-priority destinations: Borobudur, Likupang, Mandalika, Labuan Bajo, and Lake Toba. Your role is to answer factual questions about these destinations — including location, brief history, main attractions, best time to visit, opening hours, entrance fees, and other general information. Always detect the language used by the user and respond in the same language. Provide answers that are accurate, concise, and easy to understand."

# =========================
# PERTANYAAN TEST
# =========================
test_questions = [
    # === DANAU TOBA ===
    "Apa itu Danau Toba dan di mana letaknya?",
    "Bagaimana sejarah terbentuknya Danau Toba?",
    "Apa yang membuat Danau Toba unik dibanding danau lain di dunia?",
    "Berapa luas Danau Toba?",
    "Apa itu Pulau Samosir dan bagaimana cara mencapainya?",
    "Buat itinerary 2 hari di Danau Toba",
    "Buat itinerary 3 hari di Danau Toba untuk keluarga",
    "Kapan waktu terbaik mengunjungi Danau Toba?",
    "Apa saja atraksi utama di sekitar Danau Toba?",
    "Bagaimana cara menuju Danau Toba dari Jakarta?",
    "Berapa harga tiket masuk ke kawasan Danau Toba?",
    "Apa saja kuliner khas yang wajib dicoba di Danau Toba?",
    "Di mana tempat menginap terbaik di Danau Toba?",
    "Apa saja budaya dan tradisi suku Batak di Danau Toba?",
    "Apa itu Sigale-gale dan di mana bisa melihatnya?",
    # === BOROBUDUR ===
    "Apa itu Candi Borobudur dan di mana letaknya?",
    "Kapan Candi Borobudur dibangun dan oleh siapa?",
    "Buat itinerary 1 hari mengunjungi Borobudur",
    "Berapa harga tiket masuk Candi Borobudur?",
    "Apa waktu terbaik untuk mengunjungi Borobudur?",
    # === LABUAN BAJO ===
    "Apa daya tarik utama Labuan Bajo?",
    "Bagaimana cara menuju Labuan Bajo?",
    "Apa saja pulau yang bisa dikunjungi dari Labuan Bajo?",
    "Buat itinerary 3 hari di Labuan Bajo",
    "Di mana bisa melihat Komodo di Labuan Bajo?",
    # === MANDALIKA ===
    "Apa yang terkenal dari Mandalika?",
    "Di mana letak Mandalika?",
    "Apa saja pantai terbaik di Mandalika?",
    "Kapan event MotoGP Mandalika biasanya diadakan?",
    "Buat itinerary 2 hari di Mandalika",
    # === LIKUPANG ===
    "Di mana letak Likupang?",
    "Apa daya tarik wisata di Likupang?",
    "Apa saja aktivitas yang bisa dilakukan di Likupang?",
    # === LINTAS DESTINASI ===
    "Apa saja 5 destinasi super prioritas Indonesia?",
    "Bandingkan Danau Toba dan Labuan Bajo sebagai destinasi wisata",
    "Destinasi mana yang cocok untuk wisata keluarga, Borobudur atau Mandalika?",
    "Destinasi super prioritas mana yang paling cocok untuk snorkeling?",
    # === BAHASA INGGRIS ===
    "What are the main attractions at Lake Toba?",
    "How do I get to Labuan Bajo from Bali?",
    "What is the best time to visit Borobudur temple?",
]

# =========================
# LOAD MODEL (merged — tanpa PeftModel)
# =========================
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

print("Loading merged model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
model.eval()
print("Model ready!\n")

# =========================
# INFERENCE FUNCTION
# =========================
def generate_response(question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    response_ids = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(response_ids, skip_special_tokens=True).strip()

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
    "model": model_path,
    "timestamp": datetime.now().isoformat(),
    "total_questions": len(results),
    "results": results
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDone! Results saved to {output_file}")