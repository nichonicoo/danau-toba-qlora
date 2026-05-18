import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

base_model_name = "Qwen/Qwen2-7B-Instruct"
adapter_path = "./qwen-finetuned-final"
output_path = "./qwen-toba-merged"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
# Load base model (HARUS fp16/bf16, bukan 4bit)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# Load adapter
model = PeftModel.from_pretrained(base_model, adapter_path)

# Merge
model = model.merge_and_unload()

# Save full model
model.save_pretrained(output_path)
tokenizer.save_pretrained(output_path)

print("✅ Model merged dan disimpan di:", output_path)