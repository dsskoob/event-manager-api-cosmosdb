from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Optional
from database import container
from models import Participante, Evento
from azure.cosmos import exceptions
from datetime import datetime

app = FastAPI(title='API de Gestion de Eventos y Participantes')

# Endpoint de Eventos
@app.get('/')
def home():
    return "Hola Mundo"

@app.post('/events/', response_model=Evento, status_code=201)
def create_event(event: Evento):
    try:
        # insertar elemento
        container.create_item(body=event.dict())
        return event
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=400, detail="El evento ya existe")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 

@app.get('/events/{event_id}')
def get_event(event_id:str = Path(..., description="Id del evento a recuperar")):
    try:
        event = container.read_item(item=event_id, partition_key=event_id)
        return event
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 

@app.get('/events/', response_model=List[Evento])
def get_list_event():
    try:
        script = 'select * from c WHERE 1 = 1'
        items = list(container.query_items(query=script,enable_cross_partition_query=True))
        return items
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="No contiene eventos")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 

@app.put('/events/{event_id}', response_model=Evento)
def update_event(event_id:str, updated_event: Evento):
    try:
        existing_event = container.read_item(item=event_id, partition_key=event_id)
        existing_event.update(updated_event.dict(exclude_unset=True))

        if existing_event['capacity'] < len(existing_event['participants']):
            return existing_event

        container.replace_item(item=event_id, body=existing_event)
        return existing_event
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 
