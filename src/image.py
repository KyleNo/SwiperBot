import requests
import json
import asyncio
import os
import numpy as np
import cv2
from imageio import imread
import io
from discord import File

from google.cloud import vision
import google.auth

credentials, project = google.auth.default()

async def getImage(client, message, args):
    if len(args) > 0:
        url = args[0]
        image = vision.Image()
        image.source.image_uri = url
    else:
        content = await message.attachments[0].read()
        image = vision.Image(content=content)
    return image

async def describe_image(message, args):
    if len(args) < 1 and len(message.attachments) < 1:
        return await message.channel.send("Please provide an image to describe.")
    
    client = vision.ImageAnnotatorClient(credentials=credentials)
    try:
        image = await getImage(client, message, args)
    except:
        return await message.channel.send("Error retrieving image")
    response = client.label_detection(image=image)
    labels = response.label_annotations
    output = ", ".join([label.description + " (score: " + str(label.score)[:4] + ")" for label in labels])
    return await message.channel.send(output)       

async def find_objects(message, args):
    if len(args) < 1 and len(message.attachments) < 1:
        return await message.channel.send("Please provide an image.")
    
    client = vision.ImageAnnotatorClient(credentials=credentials)
    try:
        image = await getImage(client, message, args)
    except:
        return await message.channel.send("Error retrieving image")
    if len(args) > 0:
        url = args[0]
        nparr = imread(url)
    else:
        image_bytes = await message.attachments[0].read()
        nparr = imread(image_bytes)


    objects = client.object_localization(image=image).localized_object_annotations
    
    height = nparr.shape[0]
    width = nparr.shape[1]
    
    nparr = cv2.cvtColor(nparr, cv2.COLOR_BGR2RGB)

    for obj in objects:
        print(obj.name)
        verts = obj.bounding_poly.normalized_vertices
        xmin = int(min([vert.x for vert in verts]) * width)
        xmax = int(max([vert.x for vert in verts]) * width)
        ymin = int(min([vert.y for vert in verts]) * height)
        ymax = int(max([vert.y for vert in verts]) * height)
        cv2.rectangle(nparr, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
        cv2.putText(nparr, obj.name, (xmin, ymax + 25), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2)
    cv2.imwrite('identified_obj.png', nparr)
    
    #image_bytes = nparr.tobytes()
    #data = io.BytesIO(nparr)

    await message.channel.send(file=File('identified_obj.png'))



async def upscale(message, args, style):
    if len(args) < 1 and len(message.attachments) < 1:
        return await message.channel.send("Please provide an image to upscale.")
    if len(args) > 0:
        url = args[0]
    else:
        url = message.attachments[0].url
    data = {
        'style': style,
        'noise': '3',
        'x2': 2,
        'input': url
    }

    r = requests.post(
        url='https://bigjpg.com/api/task/',
        headers={'X-API-KEY': os.environ['BIGJPG_KEY']},
        data={'conf': json.dumps(data)}
    )

    r = r.json()
    taskid = r['tid']
    remaining = r['remaining_api_calls']
    
    url = 'https://bigjpg.com/api/task/' + taskid
    count = 0
    while taskid not in r and url not in r[taskid]:
        r = requests.get(url=url)
        r = r.json()
        await asyncio.sleep(10)
        count += 1
        if count > 60:
            return await message.channel.send("Error receiving task " + taskid)


    img = r[taskid]['url']
    print(img)
    s = img + '\nThere are ' + str(remaining) + ' remaining API calls'
    print(s)
    return await message.channel.send(s)
