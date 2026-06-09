from x1_scraping_citynames import citynames
from x2_scraping_cityrooms import cityrooms
from x3_data_wrangling import wrangling
from x4_dataframe_conversion import to_dataframe

pipeline = [
    citynames,
    cityrooms,
    wrangling,
    to_dataframe
]

print("\n🚀 Avvio della pipeline di scraping e processing...")

for step in pipeline:
    try:
        print(f"\n🔄 In corso: {step.__name__}...")
        step()
    except Exception as e:
        print(f"\n❌ Errore bloccante durante {step.__name__}: {e}")
        print("🛑 Pipeline interrotta per evitare corruzione dei dati successivi.")
        break
else:
    print("\n✨ Pipeline completata con successo! Tutti i file sono pronti.\n")