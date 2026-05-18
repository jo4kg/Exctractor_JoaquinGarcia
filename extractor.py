"""
Automatización de descarga de trades - PMP Platform
"""

import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# ============================================================
#  CONFIGURACIÓN
# ============================================================

URL_LOGIN         = "https://pmp.abscapco.com/PMP/Login/Login/0"
URL_TRADES        = "https://pmp.abscapco.com/PMP/SearchTradeDetails"
BASE_URL          = "https://pmp.abscapco.com"
EXCEL_PATH        = "trades.xlsx"
COLUMNA_IDS       = "TradeId"
CARPETA_DESCARGAS = r"C:\Users\JoaquinGarciaAiello\Desktop\PDF_Trades"
SESION_DIR        = r"C:\Users\JoaquinGarciaAiello\Desktop\Repository\chrome_session"

# ============================================================


async def desmarcar_as_of_date(page):
    try:
        checkbox = page.locator("input[type='checkbox']").first
        if await checkbox.is_checked():
            await checkbox.uncheck()
            await page.wait_for_timeout(500)
            print("   🗓️  'As of Date' desmarcado")
    except Exception:
        pass


async def buscar_trade(page, trade_id):
    await page.locator("#tradeDiv span.select2-selection--single").click()
    await page.wait_for_timeout(700)
    search_input = page.locator("input.select2-search__field")
    await search_input.wait_for(timeout=5_000)
    await search_input.fill("")
    await search_input.type(trade_id, delay=80)
    print(f"   ⌨️  Tipeando: {trade_id}")
    await page.wait_for_timeout(1500)
    opcion = page.locator(f"li.select2-results__option:has-text('{trade_id}')").first
    await opcion.wait_for(state="visible", timeout=8_000)
    await opcion.click()
    await page.wait_for_timeout(1000)
    print("   ✅ Trade seleccionado")


async def main():
    carpeta = Path(CARPETA_DESCARGAS)
    carpeta.mkdir(exist_ok=True)

    print(f"📄 Leyendo IDs desde: {EXCEL_PATH}")
    try:
        df = pd.read_excel(EXCEL_PATH)
    except FileNotFoundError:
        print(f"❌ No se encontró '{EXCEL_PATH}'.")
        return

    if COLUMNA_IDS not in df.columns:
        print(f"❌ No se encontró la columna '{COLUMNA_IDS}'.")
        print(f"   Columnas disponibles: {list(df.columns)}")
        return

    ids = df[COLUMNA_IDS].dropna().astype(str).str.strip().tolist()
    print(f"   → {len(ids)} IDs encontrados\n")

    resultados = []

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESION_DIR,
            headless=False,
            accept_downloads=True,
            args=["--start-maximized"],
            no_viewport=True,
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(URL_LOGIN)
        await page.wait_for_load_state("networkidle")

        if "Login" in page.url or "login" in page.url:
            print("🔐 Loguéate en el navegador. El script espera...")
            await page.wait_for_url(
                lambda url: "Login" not in url and "login" not in url,
                timeout=120_000
            )
            print("✅ Login detectado. Continuando...\n")
        else:
            print("✅ Sesión activa. Continuando...\n")

        for i, trade_id in enumerate(ids, 1):
            print(f"[{i}/{len(ids)}] Procesando: {trade_id}")
            try:
                # 1. Ir a Trade Search
                await page.goto(URL_TRADES)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(1000)

                # 2. Desmarcar "As of Date"
                await desmarcar_as_of_date(page)

                # 3. Buscar y seleccionar el trade
                await buscar_trade(page, trade_id)

                # 4. Esperar tabla y clickear la fila
                await page.wait_for_selector(f"td:has-text('{trade_id}')", timeout=10_000)
                fila = page.locator(f"tr:has-text('{trade_id}')").first
                await fila.click()
                await page.wait_for_timeout(2000)

                # 5. Esperar que abra el modal #myModal
                await page.wait_for_selector("#myModal.in", timeout=10_000)
                await page.wait_for_timeout(1000)
                print("   📋 Modal abierto")

                # 6. Buscar links de descarga dentro del modal
                links = page.locator(f"#myModal a[href*='/PMP/File/Download/']:has-text('{trade_id}')")
                count = await links.count()

                if count == 0:
                    print(f"   ⚠️  Sin archivos con '{trade_id}' en el nombre")
                    resultados.append({"ID": trade_id, "Estado": "Sin archivos", "Archivos descargados": 0})
                    continue

                print(f"   📂 {count} archivo(s) encontrado(s)")

                # 7. Recolectar hrefs antes de navegar (solo PDFs)
                hrefs = []
                nombres = []
                for j in range(count):
                    link = links.nth(j)
                    nombre_raw = (await link.inner_text()).strip()
                    if not nombre_raw.lower().endswith('.pdf'):
                        print(f"   ⏭️  Ignorando (no es PDF): {nombre_raw}")
                        continue
                    href = await link.get_attribute("href")
                    nombre = nombre_raw.replace("/", "-").replace("\\", "-")
                    hrefs.append(href)
                    nombres.append(nombre)

                # 8. Descargar clickeando un link programático en la página
                archivos_descargados = 0
                for href, nombre in zip(hrefs, nombres):
                    url_descarga = f"{BASE_URL}{href}"
                    print(f"   📥 Descargando: {nombre}")
                    try:
                        async with page.expect_download(timeout=30_000) as download_info:
                            await page.evaluate(f"""
                                const a = document.createElement('a');
                                a.href = '{url_descarga}';
                                a.download = '';
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                            """)
                        download = await download_info.value
                        destino = carpeta / f"{nombre}.pdf"
                        await download.save_as(str(destino))
                        archivos_descargados += 1
                        print(f"   ✅ Guardado: {destino}")
                        await page.wait_for_timeout(500)
                    except Exception as e_dl:
                        print(f"   ❌ Error descargando '{nombre}': {e_dl}")

                resultados.append({"ID": trade_id, "Estado": "OK", "Archivos descargados": archivos_descargados})

            except Exception as e:
                print(f"   ❌ Error: {e}")
                resultados.append({"ID": trade_id, "Estado": f"Error: {e}", "Archivos descargados": 0})

        await context.close()

    # Reporte final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)

    df_log = pd.DataFrame(resultados)
    print(f"✅ Exitosos        : {len(df_log[df_log['Estado'] == 'OK'])}")
    print(f"❌ Con error       : {len(df_log[df_log['Estado'] != 'OK'])}")
    print(f"📁 PDFs descargados: {df_log['Archivos descargados'].sum()}")

    log_path = f"log_descargas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df_log.to_excel(log_path, index=False)
    print(f"📋 Log guardado en: {log_path}")
    print("\n✔️  Proceso finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
