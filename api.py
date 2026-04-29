import os
import uuid
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
import uvicorn

os.makedirs("imagenes", exist_ok=True)

class Mensaje(BaseModel):
    tipo: str        
    subtipo: str     
    texto: str       
    hora: str
    metadata: Optional[str] = None 

class Conversacion(BaseModel):
    titulo: str
    mensajes: List[Mensaje]

# NUEVO MODELO: Para las características de la solución
class Feature(BaseModel):
    icono: str
    titulo: str
    descripcion: str

class ChatData(BaseModel):
    empresa: str
    pagina_web: str
    caso_uso: str         # Ya no hay texto por defecto
    promesa_texto: str    # Ya no hay texto por defecto
    conversaciones: List[Conversacion]
    features: List[Feature] # Nueva lista dinámica de características
    evidencia_texto: str  # Nuevo texto dinámico para el footer

app = FastAPI()
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

@app.post("/generar-imagen")
def generar_imagen(datos: ChatData, request: Request):
    
    # 1. Logo del Cliente (Favicon)
    url_limpia = datos.pagina_web if datos.pagina_web.startswith("http") else f"http://{datos.pagina_web}"
    dominio = urlparse(url_limpia).netloc.replace("www.", "")
    logo_cliente_url = f"https://www.google.com/s2/favicons?domain={dominio}&sz=128"
    logo_html = f'<img src="{logo_cliente_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'

    # 2. Logo de Platica
    platica_logo_url = "https://platica.mx/favicon.png"

    # 3. Construir los teléfonos
    telefonos_html = ""
    iconos_titulos = ["🔍", "🛡️", "✅"] 

    for i, conv in enumerate(datos.conversaciones):
        mensajes_html = ""
        icono_paso = iconos_titulos[i] if i < len(iconos_titulos) else "💬"

        for msg in conv.mensajes:
            clase_tipo = "sent" if msg.tipo == "cliente" else "received"
            
            if msg.subtipo == "imagen":
                contenido = f'<img src="{msg.texto}" style="width:100%; border-radius:5px; display:block; margin-bottom:5px;">'
            elif msg.subtipo == "archivo":
                peso = msg.metadata if msg.metadata else "PDF"
                contenido = f"""
                <div style="display:flex; align-items:center; background:rgba(0,0,0,0.05); padding:10px; border-radius:5px; margin-bottom:5px;">
                    <span style="font-size:24px; margin-right:10px;">📄</span>
                    <div style="overflow:hidden;">
                        <div style="font-size:13px; font-weight:500; white-space:nowrap; text-overflow:ellipsis; color:#111;">{msg.texto}</div>
                        <div style="font-size:11px; color:#666;">{peso}</div>
                    </div>
                </div>
                """
            else:
                contenido = f'<div style="color:#111;">{msg.texto}</div>'

            mensajes_html += f"""
            <div class="message {clase_tipo}">
                {contenido}
                <span class="time">{msg.hora}</span>
            </div>
            """
        
        telefonos_html += f"""
        <div class="phone-column">
            <div class="phone-title">{icono_paso} {conv.titulo}</div>
            <div class="phone-container">
                <div class="chat-header">
                    <div class="back-btn">←</div>
                    <div class="profile-pic">{logo_html}</div>
                    <div class="contact-info">
                        <div class="contact-name">{datos.empresa}</div>
                        <div class="contact-status">Cuenta de empresa oficial</div>
                    </div>
                </div>
                <div class="chat-body">{mensajes_html}</div>
                <div class="chat-footer"><div class="input-bar"><span>Escribe un mensaje</span><span style="float:right;">📸 🎤</span></div></div>
            </div>
        </div>
        """

    # 4. Construir las características (features) dinámicamente
    features_html = ""
    for feat in datos.features:
        features_html += f"""
        <div class="feature-item">
            <div class="feat-icon">{feat.icono}</div>
            <div class="feat-content">
                <h4>{feat.titulo}</h4>
                <p>{feat.descripcion}</p>
            </div>
        </div>
        """

    # 5. Plantilla Final con Todo Dinámico
    html_completo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
            
            #capture-area {{ width: 1600px; padding: 50px 60px; background-color: #ffffff; color: #1e293b; display: flex; flex-direction: column; gap: 30px; }}
            
            /* HEADER */
            .header-container {{ display: flex; flex-direction: column; gap: 15px; margin-bottom: 10px; position: relative; }}
            
            .platica-branding {{ display: flex; align-items: center; gap: 10px; position: absolute; top: 0; right: 0; margin-top: -20px; }}
            .platica-logo-img {{ height: 105px; width: auto; }} 
            .platica-name {{ font-size: 95px; font-weight: 500; color: #047857; letter-spacing: -4px; line-height: 1; text-transform: lowercase; }} 

            .use-case {{ color: #047857; font-weight: 600; font-size: 20px; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; max-width: 800px; }}
            .promise-text {{ font-size: 24px; font-weight: 500; color: #0f172a; line-height: 1.5; max-width: 950px; border-left: 5px solid #047857; padding-left: 20px; }}
            
            /* CONTENT */
            .main-content {{ display: flex; gap: 40px; }}
            .phones-section {{ flex: 1; display: flex; flex-direction: column; }}
            .visualizacion-header {{ text-align: center; font-size: 18px; font-weight: 600; color: #047857; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; }}
            .visualizacion-header::before, .visualizacion-header::after {{ content: ""; flex: 1; border-bottom: 1px solid #cbd5e1; }}
            
            .phones-grid {{ display: flex; gap: 30px; justify-content: center; }}
            .phone-column {{ display: flex; flex-direction: column; align-items: center; gap: 15px; }}
            .phone-title {{ font-size: 18px; font-weight: 600; color: #047857; }}
            
            .phone-container {{ width: 320px; height: 600px; background-color: #e5ddd5; border: 10px solid #1e293b; border-radius: 35px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 15px 25px rgba(0,0,0,0.15); position: relative; }}
            .phone-container::before {{ content:""; position:absolute; top:0; left:50%; transform:translateX(-50%); width:120px; height:25px; background:#1e293b; border-bottom-left-radius:15px; border-bottom-right-radius:15px; z-index:10; }}
            
            .chat-header {{ background-color: #075e54; color: white; padding: 25px 15px 10px; display: flex; align-items: center; }}
            .profile-pic {{ width: 38px; height: 38px; background-color: #fff; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 12px; font-size: 18px; overflow: hidden; }}
            .chat-body {{ flex-grow: 1; padding: 15px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-size: contain; display: flex; flex-direction: column; gap: 8px; }}
            .message {{ max-width: 85%; padding: 8px 10px; border-radius: 8px; font-size: 14px; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); line-height: 1.4; }}
            .message.sent {{ background-color: #dcf8c6; align-self: flex-end; border-top-right-radius: 0; }}
            .message.received {{ background-color: #ffffff; align-self: flex-start; border-top-left-radius: 0; }}
            .time {{ font-size: 10px; color: #888; float: right; margin-top: 4px; margin-left: 8px; }}
            
            .chat-footer {{ background-color: #f0f0f0; padding: 10px; }}
            .input-bar {{ background-color: #fff; padding: 10px 15px; border-radius: 20px; color: #999; font-size: 13px; }}
            
            /* PANEL DERECHO */
            .features-panel {{ width: 380px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; padding: 30px; display: flex; flex-direction: column; gap: 20px; }}
            .features-title {{ font-size: 20px; font-weight: 700; color: #0f172a; text-align: center; margin-bottom: 10px; }}
            .feature-item {{ display: flex; gap: 15px; align-items: flex-start; padding-bottom: 15px; border-bottom: 1px solid #e2e8f0; }}
            .feature-item:last-child {{ border-bottom: none; }}
            .feat-icon {{ font-size: 28px; background: #ecfdf5; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 1px solid #a7f3d0; }}
            .feat-content h4 {{ color: #047857; font-size: 16px; margin-bottom: 5px; }}
            .feat-content p {{ color: #475569; font-size: 13px; line-height: 1.4; }}
            
            /* FOOTER */
            .bottom-banner {{ background-color: #f0fdf4; border: 1px solid #d1fae5; border-radius: 15px; padding: 35px; text-align: center; display: flex; align-items: center; justify-content: center; }}
            .evidencia-texto {{ font-size: 26px; color: #1e293b; line-height: 1.4; max-width: 1400px; }}
            .evidencia-texto strong {{ color: #047857; font-weight: 700; }}
            
        </style>
    </head>
    <body>
        <div id="capture-area">
            
            <div class="header-container">
                <div class="use-case"><span>🌿</span> Caso de uso: {datos.caso_uso}</div>
                <div class="promesa-text">{datos.promesa_texto}</div>
                
                <div class="platica-branding">
                    <img src="{platica_logo_url}" class="platica-logo-img">
                    <span class="platica-name">platica</span>
                </div>
            </div>
            
            <div class="main-content">
                <div class="phones-section">
                    <div class="visualizacion-header">Visualización</div>
                    <div class="phones-grid">{telefonos_html}</div>
                </div>
                
                <div class="features-panel">
                    <div class="features-title">Qué incluye nuestra solución</div>
                    {features_html}
                </div>
            </div>
            
            <div class="bottom-banner">
                <div class="evidencia-texto">
                    {datos.evidencia_texto}
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1650, "height": 1100})
        page.set_content(html_completo)
        page.wait_for_load_state("networkidle")
        img = page.locator("#capture-area").screenshot(type="jpeg", quality=90)
        browser.close()
        
    nombre = f"{uuid.uuid4()}.jpg"
    with open(f"imagenes/{nombre}", "wb") as f: f.write(img)
    return JSONResponse(content={"url": f"{request.base_url}imagenes/{nombre}"})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=10000)
