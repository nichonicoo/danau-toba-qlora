import pandas as pd
import json

# 1. Baca file Excel kamu (sesuaikan nama filenya)
df = pd.read_excel("bmkg_dataset.xlsx")

jsonl_lines = []

# 2. Iterasi setiap baris dan bentuk format pesan
for index, row in df.iterrows():
    data_format = {
        "messages": [
            {"role": "system", "content": str(row["sys_prompt"])},
            {"role": "user", "content": str(row["question"])},
            {"role": "assistant", "content": str(row["response"])}
        ]
    }
    jsonl_lines.append(json.dumps(data_format, ensure_ascii=False))

# 3. Simpan ke file .jsonl
with open("dataset_trim_excel_bmkg.jsonl", "w", encoding="utf-8") as f:
    f.write("\n".join(jsonl_lines))

print("Konversi selesai! File dataset_trim_excel_bmkg.jsonl berhasil dibuat.")