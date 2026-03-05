from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

base = "meta-llama/Meta-Llama-3-8B"


model = AutoModelForCausalLM.from_pretrained(
    base,
    torch_dtype=torch.float16,
    device_map="auto"
)

model = PeftModel.from_pretrained(
    model,
    "output_toba_llama/checkpoint-500"
)

tokenizer = AutoTokenizer.from_pretrained(base)

prompt = "Apa itu Danau Toba?"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    out = model.generate(
        **inputs,
        max_new_tokens=120,
        temperature=0.7,
        top_p=0.9
    )
print(tokenizer.decode(out[0], skip_special_tokens=True))