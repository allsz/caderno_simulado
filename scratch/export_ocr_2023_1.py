import pymupdf
import winocr
from PIL import Image
import io
import asyncio
from pathlib import Path

pdf_path = Path('provas/REVALIDA-2023_1_PV_objetiva_regular.pdf')
doc = pymupdf.open(str(pdf_path))
print(f'Total de páginas no PDF {pdf_path.name}: {len(doc)}')

async def ocr(pix):
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    return (await winocr.recognize_pil(img, lang='pt')).text

async def export_all():
    pages_text = []
    for p_no in range(len(doc)):
        p = doc[p_no]
        w, h = p.rect.width, p.rect.height
        rect_left = pymupdf.Rect(15, 30, w/2 + 5, h - 25)
        rect_right = pymupdf.Rect(w/2 - 5, 30, w - 15, h - 25)
        
        pix_l = p.get_pixmap(dpi=200, clip=rect_left)
        pix_r = p.get_pixmap(dpi=200, clip=rect_right)
        
        t_l = await ocr(pix_l)
        t_r = await ocr(pix_r)
        
        pages_text.append(f'=== PAGINA {p_no+1} COLUNA ESQUERDA ===\n' + t_l)
        pages_text.append(f'=== PAGINA {p_no+1} COLUNA DIREITA ===\n' + t_r)

    Path('scratch/revalida_2023_1_full_ocr.txt').write_text('\n\n'.join(pages_text), encoding='utf-8')
    print('OCR completo salvo em scratch/revalida_2023_1_full_ocr.txt')

asyncio.run(export_all())
