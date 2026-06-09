def to_dataframe():

    import json
    import pandas as pd

    # 1. Carica il file JSON definitivo
    with open('data/therooms.json', 'r', encoding='utf-8') as file:
        room_data = json.load(file)

    rows = []

    # 2. Ciclo sui dati per appiattire la struttura
    for city, rooms in room_data.items():
        for room_id, info in rooms.items():
            row = {
                "city": city,
                "id_room": room_id,
                "price": info[0],
                "max_tenants": info[1],
                "mq": info[3],
                "has_large_bed": info[4],
                "baths": info[2]
            }
            rows.append(row)

    # 3. Creazione del DataFrame
    df = pd.DataFrame(rows)

    # 4. Ordina le colonne nell'ordine richiesto
    columns_order = ["city", "id_room", "price", "max_tenants", "mq", "has_large_bed", "baths"]
    df = df[columns_order]


    # 5. Salvataggio nei vari formati
    # Salvataggio in CSV
    df.to_csv('data/rooms_df.csv', index=False, encoding='utf-8')
    print("File CSV salvato con successo: 'rooms_dataframe.csv'")

    # Salvataggio in Parquet (di default Pandas usa 'pyarrow' se installato)
    df.to_parquet('data/rooms_df.parquet', index=False)
    print("File Parquet salvato con successo: 'rooms_dataframe.parquet'")