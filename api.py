from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
from playwright.sync_api import sync_playwright  # <-- Volvemos a la versión síncrona
import uvicorn

# 1. Definimos la estructura exacta
class Mensaje(BaseModel):
    tipo: str
    texto: str
    hora: str

class ChatData(BaseModel):
    empresa: str
    logo: str
    mensajes: List[Mensaje]

app = FastAPI(title="API Simulador de WhatsApp")

# 2. IMPORTANTE: Quitamos el "async" de aquí. Esto fuerza a FastAPI a usar un hilo separado.
@app.post("/generar-imagen")
def generar_imagen(datos: ChatData):
    
    # Lógica del Logo
    if datos.logo.startswith("http"):
        logo_html = f'<img src="{datos.logo}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">'
    else:
        logo_html = datos.logo

    # Construimos los mensajes
    mensajes_html = ""
    for msg in datos.mensajes:
        clase_tipo = "sent" if msg.tipo == "cliente" else "received"
        checkmarks = " ✓✓" if msg.tipo == "cliente" else ""
        
        mensajes_html += f"""
        <div class="message {clase_tipo}">
            {msg.texto} 
            <span class="time">{msg.hora}{checkmarks}</span>
        </div>
        """

    # Inyectamos el HTML
    html_completo = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }}
            body {{ display: flex; justify-content: center; align-items: center; background-color: #f0f2f5; height: 100vh; margin: 0; }}
            .phone-container {{ width: 350px; height: 650px; background-color: #e5ddd5; border: 8px solid #333; border-radius: 30px; display: flex; flex-direction: column; overflow: hidden; position: relative; }}
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
        <div class="phone-container" id="capture-area">
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
    </body>
    </html>
    """

    # 3. Usamos Playwright Síncrono (sin 'await')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_completo)
        
        # Esperar a que la imagen del logo cargue desde internet
        page.wait_for_load_state("networkidle")
        
        elemento_telefono = page.locator("#capture-area")
        imagen_bytes = elemento_telefono.screenshot(type="jpeg", quality=90)
        
        browser.close()
        
    return Response(content=imagen_bytes, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=9999, reload=True)