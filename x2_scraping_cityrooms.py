def cityrooms():
    import json, asyncio
    from playwright.async_api import async_playwright, Route

    # Massimo numero di stanze da processare contemporaneamente
    SEMAPHORE_LIMIT = 10

    # 1. Dizionario globale per accumulare i dati di tutte le città
    RECORDS_DATA = {}
    # Lock per gestire la scrittura concorrente sul dizionario globale senza conflitti
    data_lock = asyncio.Lock()

    async def block(route: Route):
        """Evita di scaricare immagini, fogli di stile, font e media per risparmiare tempo e banda."""
        if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
            await route.abort()
        else:
            await route.continue_()

    async def scrape_room(context, link, city):
        """Elabora la singola pagina di una stanza."""
        page = await context.new_page()
        await page.route("**/*", block)
        
        try:
            await page.goto(link, wait_until="domcontentloaded", timeout=20000)
            
            # Gestione del pulsante "Mostra di più"
            try:
                bottone = page.get_by_text("Mostra di più", exact=True)
                await bottone.click(timeout=2000)
            except Exception:
                pass
                
            # Estrazione del prezzo
            div_element = page.locator("div.flex.items-baseline >> div.font-figtree").first
            await div_element.wait_for(state="attached", timeout=5000)
            pricetext = await div_element.inner_text()

            # Estrazione caratteristiche dettagliate
            info_selector = "details.expandable-description div.grid.grid-cols-1 div.space-y-4 div.flex.items-center.gap-1"
            testi_estratti = await page.locator(info_selector).all_text_contents()
            testi_puliti = [t.strip() for t in testi_estratti if t.strip()]
            
            # Conversione del prezzo in numero intero
            price = pricetext.replace("/mese", "").strip()
            stanza_id = link[-13:-1]
            
            # Creiamo la lista con il prezzo come primo elemento, seguito dalle altre info
            room_details = [price] + testi_puliti
            
            # 2. Scrittura sicura nel dizionario globale usando il Lock
            async with data_lock:
                # Se la città non esiste ancora nel dizionario, la inizializziamo
                if city not in RECORDS_DATA:
                    RECORDS_DATA[city] = {}
                
                # Assegniamo la lista di info all'ID della stanza
                RECORDS_DATA[city][stanza_id] = room_details

            print(f"[{city.upper()}] Salvato ID: {stanza_id} | Prezzo: {price}")
            
        except Exception as e:
            print(f"[-] Errore nel caricamento della stanza {link}: {e}")
        finally:
            await page.close()

    async def scrape_with(semaphore, context, link, city):
        """Wrapper per limitare la concorrenza tramite semaforo."""
        async with semaphore:
            await scrape_room(context, link, city)

    async def main():
        # Caricamento del file JSON iniziale delle città
        with open('data/cities.json', 'r', encoding='utf-8') as file:
            city_list = json.load(file)

        async with async_playwright() as p:
            print({"status": "Scraping process started..."})
            
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            main_page = await context.new_page()
            await main_page.route("**/*", block)
            
            semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

            for city in city_list['city']:
                paging = 1
                print(f"\n--- Inizio Scraping Città: {city.upper()} ---")

                while True:
                    current_url = f"https://coliving.joivy.com/it/affitto-stanza-{city}/?page={paging}"
                    
                    try:
                        await main_page.goto(current_url, wait_until="networkidle")
                    except Exception as e:
                        print(f"[-] Errore nel caricamento della pagina elenco {paging}: {e}")
                        break
                        
                    actual_url = main_page.url

                    if current_url != actual_url:
                        print(f"\n[-----] Fine della paginazione per {city}.")
                        break
                    
                    print(f"\n[{city.upper()}] Pagina {paging} caricata con successo.\n")
                    
                    selector = "li a[title][href*='affitto']"
                    locator = main_page.locator(selector)
                    
                    links = await locator.evaluate_all("elements => elements.map(el => el.href)")
                    
                    if not links:
                        print(f"[-] Nessun link trovato alla pagina {paging}. Fine.")
                        break

                    tasks = [scrape_with(semaphore, context, link, city) for link in links]
                    await asyncio.gather(*tasks)
                    
                    paging += 1
            
            await browser.close()
            
            # 3. SALVATAGGIO FINALE DEL FILE JSON
            output_filename = 'data/roomsraw.json'
            print(f"\n--- Salvataggio dei dati in {output_filename} ---")
            with open(output_filename, 'w', encoding='utf-8') as f:
                # json.dump scrive il dizionario formattandolo in modo leggibile (indent=4)
                json.dump(RECORDS_DATA, f, ensure_ascii=False, indent=4)
                
            print(f"\n{45*'-'} FINISH {45*'-'}\n")

    asyncio.run(main())