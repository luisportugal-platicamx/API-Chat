import os
import uuid
from urllib.parse import urlparse  # <-- NUEVO: Para limpiar la URL
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
import uvicorn

os.makedirs("imagenes", exist_ok=True)

# --- MODELO ACTUALIZADO ---
class Mensaje(BaseModel):
    tipo: str        # "cliente" o "agente"
    subtipo: str     # "texto", "imagen" o "archivo"
    texto: str       # El mensaje, la URL de la imagen o el nombre del PDF
    hora: str
    metadata: Optional[str] = None # Para el tamaño del archivo (ej: "2.4 MB")

class Conversacion(BaseModel):
    titulo: str
    mensajes: List[Mensaje]

class ChatData(BaseModel):
    empresa: str
    pagina_web: str  # <-- NUEVO: Reemplaza al 'logo'
    conversaciones: List[Conversacion]

app = FastAPI()
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

@app.post("/generar-imagen")
def generar_imagen(datos: ChatData, request: Request):
    
    # --- LÓGICA PARA OBTENER EL FAVICON ---
    # 1. Limpiamos la URL para sacar solo el dominio (ej. xbox.com)
    url_limpia = datos.pagina_web if datos.pagina_web.startswith("http") else f"http://{datos.pagina_web}"
    dominio = urlparse(url_limpia).netloc.replace("www.", "")
    
    # 2. Usamos el servicio de Google para traer el icono a 128px
    logo_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=128"
    
    # 3. Lo metemos en nuestra etiqueta HTML
    logo_html = f'<img src="{logo_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'

    telefonos_html = ""
    for conv in datos.conversaciones:
        mensajes_html = ""
        for msg in conv.mensajes:
            clase_tipo = "sent" if msg.tipo == "cliente" else "received"
            
            # --- LÓGICA DE RENDERIZADO POR SUBTIPO ---
            if msg.subtipo == "imagen":
                # Burbuja de Imagen
                contenido = f'<img src="{msg.texto}" style="width:100%; border-radius:5px; display:block; margin-bottom:5px;">'
            elif msg.subtipo == "archivo":
                # Burbuja de PDF/Archivo
                peso = msg.metadata if msg.metadata else "PDF"
                contenido = f"""
                <div style="display:flex; align-items:center; background:rgba(0,0,0,0.05); padding:10px; border-radius:5px; margin-bottom:5px;">
                    <span style="font-size:24px; margin-right:10px;">📄</span>
                    <div style="overflow:hidden;">
                        <div style="font-size:13px; font-weight:500; white-space:nowrap; text-overflow:ellipsis;">{msg.texto}</div>
                        <div style="font-size:11px; color:#666;">{peso}</div>
                    </div>
                </div>
                """
            else:
                # Texto normal
                contenido = f'<div>{msg.texto}</div>'

            mensajes_html += f"""
            <div class="message {clase_tipo}">
                {contenido}
                <span class="time">{msg.hora}</span>
            </div>
            """
        
        telefonos_html += f"""
        <div class="phone-column">
            <div class="phone-title">{conv.titulo}</div>
            <div class="phone-container">
                <div class="chat-header">
                    <div class="back-btn">←</div>
                    <div class="profile-pic">{logo_html}</div>
                    <div class="contact-info">
                        <div class="contact-name">{datos.empresa}</div>
                        <div class="contact-status">Negocio - En línea</div>
                    </div>
                </div>
                <div class="chat-body">{mensajes_html}</div>
                <div class="chat-footer"><div class="input-bar"><span>Escribe un mensaje...</span></div></div>
            </div>
        </div>
        """

    html_completo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }}
            #capture-area {{ display: flex; gap: 40px; justify-content: center; padding: 50px; background-color: #d1d1d1; }}
            .phone-column {{ display: flex; flex-direction: column; align-items: center; gap: 15px; }}
            .phone-title {{ font-size: 20px; font-weight: bold; color: #222; }}
            .phone-container {{ width: 350px; height: 650px; background-color: #e5ddd5; border: 8px solid #333; border-radius: 30px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }}
            .chat-header {{ background-color: #008069; color: white; padding: 10px 15px; display: flex; align-items: center; }}
            .profile-pic {{ width: 38px; height: 38px; background-color: #fff; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 12px; font-size: 18px; overflow: hidden; }}
            .chat-body {{ flex-grow: 1; padding: 15px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-size: contain; display: flex; flex-direction: column; gap: 8px; }}
            .message {{ max-width: 85%; padding: 6px 9px; border-radius: 7px; font-size: 14px; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }}
            .message.sent {{ background-color: #dcf8c6; align-self: flex-end; }}
            .message.received {{ background-color: #ffffff; align-self: flex-start; }}
            .time {{ font-size: 10px; color: #888; float: right; margin-top: 4px; margin-left: 8px; }}
            .chat-footer {{ background-color: #f0f0f0; padding: 10px; }}
            .input-bar {{ background-color: #fff; padding: 8px 15px; border-radius: 20px; color: #999; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div id="capture-area">{telefonos_html}</div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.set_content(html_completo)
        page.wait_for_load_state("networkidle")
        img = page.locator("#capture-area").screenshot(type="jpeg", quality=90)
        browser.close()
        
    nombre = f"{uuid.uuid4()}.jpg"
    with open(f"imagenes/{nombre}", "wb") as f: f.write(img)
    return JSONResponse(content={"url": f"{request.base_url}imagenes/{nombre}"})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=10000)
