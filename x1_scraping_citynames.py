def citynames():

    import json
    from playwright.sync_api import sync_playwright

    print()

    with sync_playwright() as p:

        # 1. Starting browser
        print({"status": "Scraping process initiated..."})
        browser = p.chromium.launch(headless=True) # False per vedere il browsing
        page = browser.new_page()
        
        URL = "https://coliving.joivy.com/it/locations/"

        print(f'\nWaiting... \n\nRepeat after me: "Trying to sell a thin wrapper around an LLM API as a real app is a total clown show."\n')
        page.goto(URL, wait_until="networkidle")

        # 2. Scraping city names
        cities = page.locator('a[href^="/it/affitto-stanza-"]').all()
        city_list = []

        for city in cities:
            city_list.append(city.inner_text().strip())

        cities_json = {"city": city_list}

        # 3. Saving list in JSON
        with open('data/cities.json', 'w', encoding='utf-8') as f:
            json.dump(cities_json, f, indent=4, ensure_ascii=False)
            
        print("-> Cities saved in city_list.json\n")
        
        # 4. Closing browser
        browser.close()

    print(f"Number of cities: {len(cities_json['city'])}\n\nCity list: {cities_json['city']}\n")