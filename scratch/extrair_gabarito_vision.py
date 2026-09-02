import pymupdf
import base64
import urllib.request
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

def carregar_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def listar_modelos(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            modelos_validos = []
            for m in data.get('models', []):
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    nome = m.get('name', '').replace('models/', '')
                    modelos_validos.append(nome)
            return modelos_validos
    except Exception as e:
        print("Erro ao listar modelos:", e)
        return []

def main():
    api_key = carregar_api_key()
    print("API Key:", "Encontrada" if api_key else "Não encontrada")
    if not api_key:
        return
        
    modelos_disponiveis = listar_modelos(api_key)
    print("Modelos disponíveis:", modelos_disponiveis)
    
    # Prioriza flash models
    modelos_preferenciais = [m for m in modelos_disponiveis if 'flash' in m] + modelos_disponiveis
    
    caminho_pdf = BASE_DIR / "provas" / "GABARITO_DEFINITIVO_CADERNO_1-1.pdf"
    if not caminho_pdf.exists():
        print("Arquivo não encontrado:", caminho_pdf)
        return
        
    doc = pymupdf.open(str(caminho_pdf))
    print(f"Total de páginas no Gabarito PDF: {len(doc)}")
    
    prompt = """Você é um especialista em extração de gabaritos oficiais de concursos médicos.
Analise detalhadamente a imagem desta página do gabarito oficial definitivo do Caderno 1 do ENARE.
Extraia com 100% de exatidão o número da questão e sua resposta/gabarito correspondente.
Se a questão constar como "Anulada", "ANULADA" ou "X", retorne exatamente a string "ANULADA".
Retorne ESTRITAMENTE em formato JSON com o seguinte schema:
{
  "gabarito": {
    "1": "A",
    "2": "ANULADA",
    "3": "A"
  }
}
"""
    
    gabarito_completo = {}
    
    for idx_p in range(len(doc)):
        page = doc[idx_p]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("jpeg", jpg_quality=90)
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }
        
        sucesso = False
        for modelo in modelos_preferenciais:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    res_text = res['candidates'][0]['content']['parts'][0]['text']
                    dados = json.loads(res_text)
                    gab_pag = dados.get("gabarito", {})
                    print(f"[✓] Página {idx_p+1} processada com sucesso ({modelo}): {len(gab_pag)} respostas.")
                    gabarito_completo.update(gab_pag)
                    sucesso = True
                    break
            except Exception as e:
                pass
        
        if not sucesso:
            print(f"[X] Falha total ao processar página {idx_p+1}")
            
    doc.close()
    
    print(f"\nTotal de questões extraídas via Gemini Vision: {len(gabarito_completo)}")
    
    # Ordena numericamente
    gabarito_ordenado = {str(k): gabarito_completo.get(str(k), "N/A") for k in range(1, 101)}
    
    print("\n--- GABARITO OFICIAL DEFINITIVO ENARE CADERNO 1 (1-100) ---")
    anuladas = []
    for k, v in gabarito_ordenado.items():
        if v == "ANULADA":
            anuladas.append(k)
        print(f"Q{k}: {v}", end=" | " if int(k) % 10 != 0 else "\n")
        
    print(f"\nQuestões Anuladas ({len(anuladas)}): {', '.join(anuladas)}")
    
    # Salva json
    saida_json = BASE_DIR / "scratch" / "gabarito_enare_caderno1_vision.json"
    saida_json.write_text(json.dumps(gabarito_ordenado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvo em: {saida_json}")

if __name__ == "__main__":
    main()
