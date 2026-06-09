def wrangling():

    import json

    # 1. Caricamento dei dati originali
    with open('data/roomsraw.json', 'r', encoding='utf-8') as file:
        room_data = json.load(file)

    # Dizionario che conterrà i dati finali puliti, modificati e tipizzati
    final_data = {}
    stanze_eliminate = 0
    stanze_salvate = 0

    # 2. Elaborazione e Filtro dati
    for city, rooms in room_data.items():
        filtered_rooms = {}
        
        for room, info in rooms.items():
            # Controllo iniziale: la stanza deve avere esattamente 8 elementi
            if len(info) != 8:
                stanze_eliminate += 1
                continue
                
            # Check di conformità
            if (
                "€" not in info[0] or 
                "stanz" not in info[1] or 
                "inq" not in info[2] or 
                "lett" not in info[3] or 
                "tot" not in info[4] or 
                "cond" not in info[5] or 
                "m²" not in info[6] or 
                "Letto" not in info[7]
            ):
                stanze_eliminate += 1
                continue  # Salta alla prossima stanza
                
            # Eliminazione delle colonne superflue
            info.pop(1)  
            info.pop(1)  
            info.pop(3)  
            
            # Applicazione delle modifiche e conversioni di tipo:
            try:
                # info[0] -> Rimuove il simbolo dell'euro e converte in intero
                info[0] = int(info[0].replace("€", "").strip())
                
                # info[1] -> Prende i primi 2 caratteri e converte in intero
                info[1] = int(info[1][:2].strip())
                
                # info[2] -> Prende i primi 2 caratteri e converte in intero
                info[2] = int(info[2][:2].strip())
                
                # info[3] -> Elimina "m²" e prende gli n caratteri convertendoli in float
                info[3] = info[3].replace("m²","")
                info[3] = float(info[3][:len(info[3])].strip())
                
                # info[4] -> Trasforma in Booleano basandosi sulla presenza della parola "Singolo"
                if "Singolo" in info[4]:
                    info[4] = False
                else:
                    info[4] = True
                    
                # Se tutte le conversioni sono andate a buon fine, salva la stanza
                filtered_rooms[room] = info
                stanze_salvate += 1
                
            except ValueError:
                # In caso di mancanza conciliazione
                stanze_eliminate += 1

        # Salva la città nel nuovo dizionario solo se è rimasta almeno una stanza valida
        if filtered_rooms:
            final_data[city] = filtered_rooms

    # 3. Scrittura del file JSON definitivo
    output_filename = 'data/therooms.json'
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(final_data, file, indent=4, ensure_ascii=False)

    # 4. Resoconto finale a schermo
    print(f"Stanze eliminate totali (o con errori di conversione): {stanze_eliminate}")
    print(f"Stanze salvate e convertite con successo:              {stanze_salvate}")
    print(f"Il file finale definitivo '{output_filename}' è pronto.")