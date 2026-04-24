import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def debug_database():
    # URL que você forneceu (já apontando para odin_db)
    uri = "mongodb+srv://alpargatas_user:hGJZbmrO46NPksBb@alpargatas-insights-clu.2iuzc4b.mongodb.net/odin_db?retryWrites=true&w=majority&appName=alpargatas-insights-cluster"
    
    print("--- INICIANDO DEBUG DE CONEXÃO ---")
    try:
        client = AsyncIOMotorClient(uri)
        # Força uma conexão
        await client.admin.command('ping')
        print("✅ Conexão estabelecida com sucesso!")

        # Lista os bancos disponíveis para o seu usuário
        dbs = await client.list_database_names()
        print(f"📂 Bancos de dados visíveis: {dbs}")

        db = client["odin_db"]
        
        # Lista as coleções dentro do odin_db
        collections = await db.list_collection_names()
        print(f"📋 Coleções encontradas: {collections}")

        # Testa a contagem na coleção que vimos no seu Compass
        if "bairro_indicadores" in collections:
            count = await db["bairro_indicadores"].count_documents({})
            print(f"📊 Total de documentos em 'bairro_indicadores': {count}")
            
            # Pega um exemplo para checar o nome dos campos
            doc = await db["bairro_indicadores"].find_one()
            print(f"🔍 Exemplo de chaves no documento: {list(doc.keys()) if doc else 'Nenhum dado'}")
        else:
            print("❌ ERRO: Coleção 'bairro_indicadores' não encontrada no banco 'odin_db'.")

    except Exception as e:
        print(f"💥 FALHA CRÍTICA: {e}")

if __name__ == "__main__":
    asyncio.run(debug_database())