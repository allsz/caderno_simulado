import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

# Gabaritos Oficiais
GABARITO_CADERNO1 = {
    "1": "A", "2": "ANULADA", "3": "A", "4": "D", "5": "C", "6": "B", "7": "ANULADA", "8": "B", "9": "ANULADA", "10": "ANULADA",
    "11": "ANULADA", "12": "D", "13": "C", "14": "B", "15": "A", "16": "B", "17": "D", "18": "D", "19": "D", "20": "C",
    "21": "A", "22": "A", "23": "B", "24": "D", "25": "A", "26": "C", "27": "D", "28": "B", "29": "A", "30": "C",
    "31": "B", "32": "D", "33": "C", "34": "B", "35": "D", "36": "C", "37": "D", "38": "D", "39": "D", "40": "ANULADA",
    "41": "C", "42": "D", "43": "ANULADA", "44": "B", "45": "B", "46": "C", "47": "C", "48": "D", "49": "B", "50": "C",
    "51": "C", "52": "A", "53": "C", "54": "C", "55": "A", "56": "D", "57": "D", "58": "A", "59": "B", "60": "C",
    "61": "A", "62": "B", "63": "B", "64": "D", "65": "A", "66": "A", "67": "C", "68": "B", "69": "C", "70": "B",
    "71": "B", "72": "A", "73": "C", "74": "A", "75": "A", "76": "ANULADA", "77": "B", "78": "D", "79": "B", "80": "A",
    "81": "D", "82": "D", "83": "B", "84": "C", "85": "B", "86": "D", "87": "B", "88": "ANULADA", "89": "A", "90": "C",
    "91": "B", "92": "A", "93": "C", "94": "A", "95": "B", "96": "D", "97": "C", "98": "C", "99": "A", "100": "ANULADA"
}

GABARITO_TIPO3 = {
    "1": "C", "2": "C", "3": "D", "4": "C", "5": "D", "6": "C", "7": "C", "8": "E", "9": "D", "10": "D",
    "11": "E", "12": "A", "13": "B", "14": "D", "15": "D", "16": "B", "17": "C", "18": "E", "19": "E", "20": "C",
    "21": "C", "22": "D", "23": "B", "24": "B", "25": "D", "26": "C", "27": "E", "28": "A", "29": "C", "30": "A",
    "31": "D", "32": "E", "33": "C", "34": "B", "35": "B", "36": "A", "37": "D", "38": "E", "39": "D", "40": "B",
    "41": "C", "42": "C", "43": "C", "44": "ANULADA", "45": "ANULADA", "46": "B", "47": "E", "48": "C", "49": "C", "50": "A",
    "51": "C", "52": "A", "53": "B", "54": "E", "55": "B", "56": "A", "57": "E", "58": "E", "59": "B", "60": "C",
    "61": "B", "62": "D", "63": "C", "64": "A", "65": "D", "66": "C", "67": "A", "68": "A", "69": "C", "70": "D",
    "71": "E", "72": "A", "73": "C", "74": "C", "75": "B", "76": "B", "77": "B", "78": "A", "79": "A", "80": "B",
    "81": "E", "82": "A", "83": "D", "84": "B", "85": "A", "86": "B", "87": "E", "88": "E", "89": "C", "90": "A",
    "91": "E", "92": "D", "93": "ANULADA", "94": "B", "95": "D", "96": "A", "97": "C", "98": "B", "99": "D", "100": "A"
}

def migrar_imagens():
    print("[*] Migrando arquivos de imagens...")
    img_dir = BASE_DIR / "saida" / "imagens"
    
    # 1. Imagens ENARE-2025-Objetiva_* -> ENARE-2025-Objetiva-AcessoDireto-Tipo3_*
    for f in img_dir.glob("ENARE-2025-Objetiva_*.png"):
        novo_nome = f.name.replace("ENARE-2025-Objetiva_", "ENARE-2025-Objetiva-AcessoDireto-Tipo3_")
        destino = img_dir / novo_nome
        shutil.copy2(f, destino)
        print(f"   [+] Copiado: {f.name} -> {novo_nome}")
        
    # 2. Imagens ENARE-2026-Objetiva_* -> ENARE-2025-Objetiva-Carderno1_*
    for f in img_dir.glob("ENARE-2026-Objetiva_*.png"):
        novo_nome = f.name.replace("ENARE-2026-Objetiva_", "ENARE-2025-Objetiva-Carderno1_")
        destino = img_dir / novo_nome
        shutil.copy2(f, destino)
        print(f"   [+] Copiado: {f.name} -> {novo_nome}")

def migrar_banco_questoes():
    print("\n[*] Migrando banco de questões cache...")
    banco_path = BASE_DIR / "saida" / "banco_questoes_cache.json"
    banco = json.loads(banco_path.read_text(encoding="utf-8"))
    
    novo_banco = []
    for q in banco:
        origem = q.get("origem", "")
        num = str(q.get("numero", ""))
        
        if origem == "ENARE-2025-Objetiva":
            q["origem"] = "ENARE-2025-Objetiva-AcessoDireto-Tipo3"
            gab_oficial = GABARITO_TIPO3.get(num, q.get("gabarito", "N/A"))
            q["gabarito"] = gab_oficial
            if q.get("imagens"):
                q["imagens"] = [img.replace("ENARE-2025-Objetiva_", "ENARE-2025-Objetiva-AcessoDireto-Tipo3_") for img in q["imagens"]]
            if q.get("imagem"):
                q["imagem"] = q["imagem"].replace("ENARE-2025-Objetiva_", "ENARE-2025-Objetiva-AcessoDireto-Tipo3_")
                
            if gab_oficial == "ANULADA":
                continue # Descarta questão anulada
            novo_banco.append(q)
            
        elif origem == "ENARE-2026-Objetiva":
            q["origem"] = "ENARE-2025-Objetiva-Carderno1"
            gab_oficial = GABARITO_CADERNO1.get(num, q.get("gabarito", "N/A"))
            q["gabarito"] = gab_oficial
            if q.get("imagens"):
                q["imagens"] = [img.replace("ENARE-2026-Objetiva_", "ENARE-2025-Objetiva-Carderno1_") for img in q["imagens"]]
            if q.get("imagem"):
                q["imagem"] = q["imagem"].replace("ENARE-2026-Objetiva_", "ENARE-2025-Objetiva-Carderno1_")
                
            if gab_oficial == "ANULADA":
                continue # Descarta questão anulada
            novo_banco.append(q)
        else:
            novo_banco.append(q)
            
    banco_path.write_text(json.dumps(novo_banco, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Banco de questões salvo com {len(novo_banco)} questões ativas.")

def migrar_cache_explicacoes():
    print("\n[*] Migrando cache de explicações...")
    cache_path = BASE_DIR / "saida" / "cache_explicacoes.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    
    novo_cache = {}
    for chave, item in cache.items():
        if chave.startswith("ENARE-2025-Objetiva_"):
            num = chave.split("_")[-1]
            nova_chave = f"ENARE-2025-Objetiva-AcessoDireto-Tipo3_{num}"
            item["gabarito"] = GABARITO_TIPO3.get(num, item.get("gabarito"))
            novo_cache[nova_chave] = item
            # Mantém cópia com chave antiga para compatibilidade se necessário
            novo_cache[chave] = item
        elif chave.startswith("ENARE-2026-Objetiva_"):
            num = chave.split("_")[-1]
            nova_chave = f"ENARE-2025-Objetiva-Carderno1_{num}"
            item["gabarito"] = GABARITO_CADERNO1.get(num, item.get("gabarito"))
            novo_cache[nova_chave] = item
            novo_cache[chave] = item
        else:
            novo_cache[chave] = item
            
    cache_path.write_text(json.dumps(novo_cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Cache de explicações atualizado com {len(novo_cache)} registros.")

if __name__ == "__main__":
    migrar_imagens()
    migrar_banco_questoes()
    migrar_cache_explicacoes()
    print("\n[✓] Migração concluída com sucesso!")
