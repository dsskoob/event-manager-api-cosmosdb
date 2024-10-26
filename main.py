from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Optional
from database import container
from models import Participante, Evento
from azure.cosmos import exceptions
from datetime import datetime

app = FastAPI(title='API de Gestion de Eventos y Participantes')

@app.get('/')
def home():
    return "Hola Mundo"



#### Endpoint de Eventos

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
            raise HTTPException(status_code=400, detail= 'No se pudo insertar porque la capacidad es menor a la cantidad de participantes')

        container.replace_item(item=event_id, body=existing_event)
        return existing_event
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 

@app.delete('/events/{event_id}', status_code=204)
def delete_event(event_id:str):
    try:
        container.delete_item(item=event_id, partition_key=event_id)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 



#### Endpoints de Participantes

@app.post("/events/{event_id}/participants/", response_model=Participante, status_code=201)
def add_participant(event_id: str, participant: Participante):

    try:
        #Obtener evento
        event = container.read_item(item=event_id, partition_key=event_id)

        #Validar que no se supere la cantidad de participantes
        if len(event['participants']) >= event['capacity'] :
            raise HTTPException(status_code=400, detail='Capacidad maxima del evento alcanzado')
        
        #Validar que el participante no existe
        if any( p['id'] == participant.id for p in event['participants'] ):
            raise HTTPException(status_code=400, detail='El partipante con este Id ya esta inscrito')

        event['participants'].append(participant.dict())

        container.replace_item(item=event_id, body=event)

        return participant
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail='Evento no encotrado')
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/events/{event_id}/participants/{participant_id}")
def get_participant(event_id: str, participant_id: str):

    try:
        #Obtener evento
        event = container.read_item(item=event_id, partition_key=event_id)

        #Obtener participante
        participant = next((p for p in event['participants'] if p['id'] == participant_id), None)
        
        if participant:
            return participant
        else:
            raise HTTPException(status_code=404, detail='Participante no encotrado')

    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail='Evento no encotrado')
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail=str(e))
 

@app.get('/events/{event_id}/participants/', response_model=List[Participante])
def get_list_participants(event_id: str):
    try:
        #Obtener evento
        event = container.read_item(item=event_id, partition_key=event_id)

        participants = event.get('participants',[])

        if participants:
            return participants
        else:
            raise HTTPException(status_code=404, detail='No hay participantes')

    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="No existe el evento")
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail= str(e))
 

@app.put("/events/{event_id}/participants/{participant_id}", response_model=Participante)
def update_participant(event_id: str, participant_id: str, updated_participant: Participante):
 
    try:
        event = container.read_item(item=event_id, partition_key=event_id)
        participant = next((p for p in event['participants'] if p['id'] == participant_id), None)
 
        if not participant:
            raise HTTPException(status_code=404, detail= "Participante no encontrado")
        
        participant.update(updated_participant.dict(exclude_unset=True))
 
        event['participants'] = [ p if p['id'] != participant_id else participant for p in event['participants']]
 
        container.replace_item(item=event_id, body=event)
 
        return participant
        
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail='Evento no encotrado')
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail=str(e))

 
@app.delete("/events/{event_id}/participants/{participant_id}", status_code=204)
def delete_participant(event_id: str, participant_id: str):
 
    try:
 
        event = container.read_item(item=event_id, partition_key=event_id)
        participant = next((p for p in event['participants'] if p['id'] == participant_id), None)
 
        if not participant:
            raise HTTPException(status_code=404, detail='Participante no encontrado')
        
        event['participants'] = [ p for p in event['participants'] if p['id'] != participant_id]
 
        container.replace_item(item=event_id, body=event)
        return
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail='Evento no encotrado')
    except exceptions.CosmosHttpResponseError as e:
        raise HTTPException(status_code=400, detail=str(e))