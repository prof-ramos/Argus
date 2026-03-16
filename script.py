
from PIL import Image, ImageDraw, ImageFont
import json

# Criar diagrama de arquitetura em alta resolução
img = Image.new('RGB', (1400, 900), color='#0f172a')
draw = ImageDraw.Draw(img)

# Definir cores do design system
colors = {
    'primary': '#38bdf8',      # teal
    'surface': '#1e293b',      # dark surface
    'text_primary': '#f1f5f9', # light text
    'text_secondary': '#cbd5e1', # muted text
    'success': '#38bdf8',
    'border': '#334155'
}

# Tentar carregar fonte monoespacial
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font_title = ImageFont.load_default()
    font_normal = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Helper para desenhar caixa
def draw_box(x, y, w, h, label, color, text_color='#f1f5f9'):
    draw.rectangle([x, y, x+w, y+h], outline=color, width=2, fill='#020617')
    text_x = x + w//2
    text_y = y + h//2
    draw.text((text_x, text_y), label, fill=text_color, font=font_normal, anchor='mm')

# Título
draw.text((700, 30), 'ARGUS — Arquitetura de Componentes', fill=colors['primary'], font=font_title, anchor='mm')

# CAMADA 1: INPUT
y_offset = 80
draw.text((700, y_offset), '1. INPUT LAYER', fill=colors['primary'], font=font_normal, anchor='mm')
draw_box(300, y_offset+30, 180, 50, 'Username', colors['primary'])
draw_box(560, y_offset+30, 180, 50, 'Email', colors['primary'])
draw_box(820, y_offset+30, 180, 50, 'Ambos', colors['primary'])

# CAMADA 2: COLLECTORS (paralelos)
y_offset = 200
draw.text((700, y_offset), '2. COLLECTION LAYER (asyncio)', fill=colors['primary'], font=font_normal, anchor='mm')
draw_box(150, y_offset+30, 150, 50, 'Maigret', colors['success'])
draw_box(380, y_offset+30, 150, 50, 'Holehe', colors['success'])
draw_box(610, y_offset+30, 150, 50, 'Sherlock', colors['success'])
draw_box(840, y_offset+30, 150, 50, 'GHunt', colors['success'])

# CAMADA 3: PROCESSING
y_offset = 320
draw.text((700, y_offset), '3. PROCESSING LAYER', fill=colors['primary'], font=font_normal, anchor='mm')
draw_box(250, y_offset+30, 140, 50, 'Normalize', colors['border'])
draw_box(490, y_offset+30, 140, 50, 'Filter (HTTP)', colors['border'])
draw_box(730, y_offset+30, 140, 50, 'Enrich', colors['border'])

# CAMADA 4: AI ANALYSIS
y_offset = 440
draw.text((700, y_offset), '4. AI ANALYSIS LAYER', fill=colors['primary'], font=font_normal, anchor='mm')
draw_box(350, y_offset+30, 180, 50, 'Prompt Builder', colors['primary'])
draw_box(650, y_offset+30, 180, 50, 'GPT-4o-mini', colors['primary'])

# CAMADA 5: OUTPUT
y_offset = 560
draw.text((700, y_offset), '5. OUTPUT LAYER', fill=colors['primary'], font=font_normal, anchor='mm')
draw_box(250, y_offset+30, 120, 50, 'CLI', colors['success'])
draw_box(460, y_offset+30, 120, 50, 'JSON', colors['success'])
draw_box(670, y_offset+30, 120, 50, 'HTML', colors['success'])
draw_box(880, y_offset+30, 120, 50, 'PDF', colors['success'])

# Dados de configuração
y_offset = 700
draw.text((150, y_offset), 'METADATA', fill=colors['text_secondary'], font=font_small)
draw.rectangle([80, y_offset+15, 250, y_offset+60], outline=colors['border'], width=1, fill='#0f172a')
draw.text((165, y_offset+30), 'platforms_metadata.json', fill=colors['text_secondary'], font=font_small, anchor='mm')

draw.text((400, y_offset), 'STORAGE', fill=colors['text_secondary'], font=font_small)
draw.rectangle([350, y_offset+15, 520, y_offset+60], outline=colors['border'], width=1, fill='#0f172a')
draw.text((435, y_offset+30), './reports/ directory', fill=colors['text_secondary'], font=font_small, anchor='mm')

draw.text((650, y_offset), 'EXTERNAL API', fill=colors['text_secondary'], font=font_small)
draw.rectangle([600, y_offset+15, 770, y_offset+60], outline=colors['border'], width=1, fill='#0f172a')
draw.text((685, y_offset+30), 'OpenAI API', fill=colors['text_secondary'], font=font_small, anchor='mm')

img.save('argus_architecture.png', 'PNG', quality=95)
print("✅ Diagrama de arquitetura salvo: argus_architecture.png")

# Salvar metadados
with open('argus_architecture.png.meta.json', 'w') as f:
    json.dump({
        "caption": "Arquitetura em 5 camadas do ARGUS",
        "description": "Fluxo de dados: Input → Collection (paralelo) → Processing → AI Analysis → Output"
    }, f)
