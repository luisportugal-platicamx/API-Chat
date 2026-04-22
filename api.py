import os
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from playwright.sync_api import sync_playwright
import uvicorn

os.makedirs("imagenes", exist_ok=True)

# --- NUEVA ESTRUCTURA DE DATOS ---
class Mensaje(BaseModel):
    tipo: str
    texto: str
    hora: str

class Conversacion(BaseModel):
    titulo: str
    mensajes: List[Mensaje]

class ChatData(BaseModel):
    empresa: str
    logo: str
    conversaciones: List[Conversacion]  # <--- Ahora esperamos una lista de conversaciones
# ---------------------------------

app = FastAPI(title="API Simulador de WhatsApp")
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

@app.post("/generar-imagen")
def generar_imagen(datos: ChatData, request: Request):
    
    # Lógica del Logo
    if datos.logo.startswith("http"):
        logo_html = f'<img src="{datos.logo}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">'
    else:
        logo_html = datos.logo

    # --- GENERAR MÚLTIPLES TELÉFONOS ---
    telefonos_html = ""
    for conv in datos.conversaciones:
        mensajes_html = ""
        for msg in conv.mensajes:
            clase_tipo = "sent" if msg.tipo == "cliente" else "received"
            checkmarks = " ✓✓" if msg.tipo == "cliente" else ""
            
            mensajes_html += f"""
            <div class="message {clase_tipo}">
                {msg.texto} 
                <span class="time">{msg.hora}{checkmarks}</span>
            </div>
            """
        
        # Armamos un teléfono completo por cada conversación
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
                <div class="chat-body">
                    {mensajes_html}
                </div>
                <div class="chat-footer">
                    <div class="input-bar"><span>Escribe un mensaje...</span></div>
                    <div class="mic-btn"><span>🎤</span></div>
                </div>
            </div>
        </div>
        """

    # --- HTML Y CSS ACTUALIZADO PARA 3 COLUMNAS ---
    html_completo = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }}
            body {{ background-color: #f0f2f5; margin: 0; }}
            
            /* El área de captura ahora es una caja flexible horizontal */
            #capture-area {{ 
                display: flex; 
                gap: 50px; 
                justify-content: center; 
                align-items: flex-start; 
                padding: 60px; 
                background-color: #e5ddd5; /* Fondo desenfocado genérico */
            }}
            
            .phone-column {{ display: flex; flex-direction: column; align-items: center; gap: 20px; }}
            .phone-title {{ font-size: 24px; font-weight: bold; color: #333; text-align: center; }}
            
            .phone-container {{ width: 350px; height: 650px; background-color: #e5ddd5; border: 8px solid #333; border-radius: 30px; display: flex; flex-direction: column; overflow: hidden; position: relative; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }}
            .chat-header {{ background-color: #008069; color: white; padding: 10px 15px; display: flex; align-items: center; z-index: 2; }}
            .back-btn {{ margin-right: 10px; font-size: 20px; }}
            .profile-pic {{ width: 40px; height: 40px; background-color: #fff; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px; font-size: 20px; overflow: hidden; }}
            .contact-info {{ flex-grow: 1; }}
            .contact-name {{ font-size: 16px; font-weight: 500; }}
            .contact-status {{ font-size: 12px; opacity: 0.8; }}
            .chat-body {{ flex-grow: 1; padding: 20px 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-size: cover; }}
            .message {{ max-width: 80%; padding: 8px 12px; border-radius: 7.5px; font-size: 14.2px; line-height: 19px; position: relative; word-wrap: break-word; }}
            .message .time {{ font-size: 11px; color: #999; float: right; margin-top: 5px; margin-left: 10px; }}
            .message.sent {{ background-color: #dcf8c6; align-self: flex-end; border-top-right-radius: 0; }}
            .message.sent::before {{ content: ""; position: absolute; top: 0; right: -8px; border-top: 10px solid #dcf8c6; border-right: 10px solid transparent; }}
            .message.received {{ background-color: #ffffff; align-self: flex-start; border-top-left-radius: 0; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); }}
            .message.received::before {{ content: ""; position: absolute; top: 0; left: -8px; border-top: 10px solid #ffffff; border-left: 10px solid transparent; }}
            .chat-footer {{ background-color: #f0f0f0; padding: 10px; display: flex; align-items: center; }}
            .input-bar {{ flex-grow: 1; background-color: #fff; padding: 10px 15px; border-radius: 20px; color: #888; font-size: 14px; display: flex; }}
            .mic-btn {{ width: 40px; height: 40px; background-color: #008069; color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div id="capture-area">
            {telefonos_html}
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        
        # NUEVO: Agrandar la ventana del navegador para que quepan 3 teléfonos sin cortarse
        page.set_viewport_size({"width": 1400, "height": 900})
        
        page.set_content(html_completo)
        page.wait_for_load_state("networkidle")
        
        elemento_telefono = page.locator("#capture-area")
        imagen_bytes = elemento_telefono.screenshot(type="jpeg", quality=90)
        browser.close()
        
    nombre_archivo = f"{uuid.uuid4()}.jpg"
    ruta_archivo = os.path.join("imagenes", nombre_archivo)
    
    with open(ruta_archivo, "wb") as f:
        f.write(imagen_bytes)
        
    url_publica = f"{request.base_url}imagenes/{nombre_archivo}"
    
    return JSONResponse(content={"mensaje": "Éxito", "url": url_publica})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=10000)
