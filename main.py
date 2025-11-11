from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import re
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API RNP", version="1.0.0")

async def retry(fn, retries=2, delay=1000):
    """Función auxiliar para reintentar operaciones"""
    for i in range(retries):
        try:
            return await fn()
        except Exception as error:
            if i == retries - 1:
                raise error
            await asyncio.sleep(delay / 1000)

async def scrape_rnp(ruc: str):
    browser = None
    page = None
    try:
        logger.info(f"Iniciando scraping para RUC: {ruc}")
        
        async with async_playwright() as p:
            # Configuración del navegador optimizada
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
            
            page = await browser.new_page()
        
            # Configuración inicial
            await page.set_viewport_size({"width": 1280, "height": 800})
            page.set_default_timeout(80000)

            # Paso 1: Navegar a la página principal
            await page.goto('https://apps.oece.gob.pe/perfilprov-ui/', wait_until='domcontentloaded')

            # Esperar campo de búsqueda
            await page.wait_for_selector('input#textBuscar', state='visible', timeout=30000)

            # Paso 2: Escribir el RUC
            await page.fill('input#textBuscar', ruc)

            # Paso 3: Click en Buscar y esperar resultados con retry
            await page.click('button#btnBuscar')
        
            # Esperar resultados con retry
            await retry(lambda: page.wait_for_selector('div#idPanelA2 span.tile__proveedor-info', timeout=45000))
        
            # Esperar que haya al menos un RNP visible y con texto
            await retry(lambda: page.wait_for_function('''() => {
                const elems = document.querySelectorAll('div#idPanelA2 span.tile__proveedor-info');
                return elems.length > 0 && Array.from(elems).some(el => el.textContent.trim().length > 0);
            }''', timeout=30000))

            # Paso 4: Extraer RNP
            rnp_elements = await page.eval_on_selector_all(
                'div#idPanelA2 span.tile__proveedor-info',
                'elements => elements.map(el => el.textContent.trim())'
            )
        
            # Filtrar y formatear resultados
            filtered_rnps = [
                re.sub(r'\s+', ' ', rnp).strip()
                for rnp in rnp_elements
                if rnp.strip()
            ]
        
            if not filtered_rnps:
                raise Exception('No se encontraron RNP para el RUC proporcionado')

            # Paso 5: Click en el enlace del proveedor
            await page.wait_for_selector(
                '#idPanelA2 > div.result-data.d-flex.flex-wrap > div > app-tile > a', 
                timeout=30000
            )
            await page.click('#idPanelA2 > div.result-data.d-flex.flex-wrap > div > app-tile > a')
            
            # Estrategia de espera para la ficha del proveedor
            main_info_selector = 'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card'
        
            try:
                await retry(lambda: page.wait_for_selector(
                    main_info_selector, 
                    state='visible',
                    timeout=10000
                ), 2, 2000)
            except Exception as selector_error:
                raise Exception(f'No se pudo cargar la ficha del proveedor: {str(selector_error)}')

            async def get_first_matching_element_text(selectors):
                for selector in selectors:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text:
                            return text.strip()
                return 'No disponible'

            # Definir selectores
            info_value_selectors = [
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.active > div.profile-content.reduced > div:nth-child(2) > span.info-value',
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.inactive > div.profile-content.reduced > ul:nth-child(1) > li > div > span.info-value'
            ]

            email_selectors = [
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.active > div.profile-content.reduced > div:nth-child(3) > div > span > a',
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.inactive > div.profile-content.reduced > div:nth-child(3) > div > span > a'
            ]

            region_selectors = [
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.active > div.profile-content > ul:nth-child(4) > li:nth-child(1) > div > span:nth-child(3)',
                'body > app-root > div > div > app-prov-ficha > div > div > div:nth-child(1) > div.col-md-7.col-12 > div.supplier-card.inactive > div.profile-content.reduced > ul:nth-child(4) > li:nth-child(1) > div > span:nth-child(3)'
            ]
        
            # Obtener datos
            info_value = await get_first_matching_element_text(info_value_selectors)
            email = await get_first_matching_element_text(email_selectors)
            region_text = await get_first_matching_element_text(region_selectors)
            
            # Ajustar región
            region = region_text if region_text != 'No disponible' else 'No disponible'

            result = {
                'ruc': ruc,
                'rnps': filtered_rnps,
                'infoValue': info_value,
                'email': email,
                'region': region,
                'status': 'success'
            }
            
            logger.info(f"Scraping completado para RUC: {ruc}")
            return result

    except Exception as error:
        logger.error(f"Error en scraping RUC {ruc}: {error}")
        return {
            'ruc': ruc,
            'error': str(error),
            'status': 'error'
        }
    finally:
        if browser:
            await browser.close()

@app.get("/")
async def root():
    return {"message": "API de consulta RNP - Bienvenido"}

@app.get("/consultar/{ruc}")
async def consultar_rnp(ruc: str):
    if not re.match(r'^\d{11}$', ruc):
        raise HTTPException(status_code=400, detail="RUC debe tener 11 dígitos")
    
    try:
        result = await scrape_rnp(ruc)
        if result.get('status') == 'error':
            raise HTTPException(status_code=404, detail=result['error'])
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# INICIO CORREGIDO - Maneja correctamente el puerto
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando API RNP en puerto {port}...")
    print(f"📝 URL: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
