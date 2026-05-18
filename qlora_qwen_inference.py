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
adapter_path = "./qwen-finetuned-final"
output_file = f"inference_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

SYSTEM_PROMPT = "You are an accurate and reliable travel information assistant, specializing in Indonesia's five super-priority destinations: Borobudur, Likupang, Mandalika, Labuan Bajo, and Lake Toba."

# =========================
# PERTANYAAN TEST
# =========================
test_questions = [
    "Buat itinerary 2 hari di Danau Toba",
    "Apa yang membuat Danau Toba unik dibanding danau lain di Indonesia?",
    "Berapa harga tiket masuk ke Danau Toba?",
    "Kapan waktu terbaik mengunjungi Danau Toba?",
    "Apa saja atraksi utama di sekitar Danau Toba?",
    "Bagaimana cara menuju Danau Toba dari Jakarta?",
    "Whats the difference between Mandalika and other places?",
    "What are the main attractions at Lake Toba?",  # test bahasa Inggris
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
# INFERENCE FUNCTION
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
            max_new_tokens=512,
            temperature=0.7,
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