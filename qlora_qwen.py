import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig
from trl import SFTTrainer

# =========================
# CONFIG
# =========================
model_name = "Qwen/Qwen2-7B-Instruct"   # ganti ke 1.5B kalau VRAM kecil
dataset_path = "data/full/full_dataset.jsonl"

# =========================
# TOKENIZER
# =========================
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True
)

tokenizer.pad_token = tokenizer.eos_token

# =========================
# QLoRA (4-bit)
# =========================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# =========================
# MODEL
# =========================
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

model.config.use_cache = False  # penting untuk training

# =========================
# LoRA CONFIG (QWEN OPTIMAL)
# =========================
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "up_proj",
        "down_proj"
    ]
)

# =========================
# DATASET
# =========================
dataset = load_dataset("json", data_files=dataset_path)

print("dataset: ", dataset)

# =========================
# FORMAT CHAT (WAJIB UNTUK QWEN)
# =========================
def format_chat(example):
    return tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False
    )

# =========================
# TRAINING ARGUMENTS
# =========================
training_args = TrainingArguments(
    output_dir="./qwen-toba",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=200,
    bf16=True,
    optim="paged_adamw_32bit",
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    report_to="none"
)

# =========================
# TRAINER
# =========================
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    peft_config=peft_config,
    tokenizer=tokenizer,
    formatting_func=format_chat,
    max_seq_length=2048,
    args=training_args
)

# =========================
# TRAIN
# =========================
trainer.train()

# =========================
# SAVE MODEL
# =========================
trainer.save_model("./qwen-finetuned-final")
tokenizer.save_pretrained("./qwen-finetuned-final")