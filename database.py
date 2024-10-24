from azure.cosmos import CosmosClient, exceptions

COSMOS_ENDPOINT = 'https://azcdb-dam.documents.azure.com:443/'
COSMOS_KEY = '0EgYze9fkgOGddU8AnolzDrgC7RuGy8LdK4v8By8h6Pk3y39axqaQ2wI0LmWw79lXnVh67En9AhEACDbi8iLzg=='

DATABASE_NAME = 'test_db'
CONTAINER_NAME = 'events'

#Inicializa cliente de cosmos
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

# Crear o obtener la base de datos
try:
    database = client.create_database_if_not_exists(id=DATABASE_NAME)
except exceptions.CosmosResourceExistsError:
    database = client.get_database_client(DATABASE_NAME)

# Crear o obtener el contenedor
try:
    container = database.create_container_if_not_exists(
        id=CONTAINER_NAME,
        partition_key={'paths': ['/id'], 'kind': 'Hash'},
        offer_throughput=400
    )
except exceptions.CosmosResourceExistsError:
    container = database.get_container_client(CONTAINER_NAME)