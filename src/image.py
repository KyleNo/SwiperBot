import requests
import json
import asyncio
import os

from google.cloud import vision
import google.auth

credentials, project = google.auth.default()

async def describe_image(message, args):
    if len(args) < 1 and len(message.attachments) < 1:
        return await message.channel.send("Please provide an image to upscale.")
    
    client = vision.ImageAnnotatorClient(credentials=credentials)
    if len(args) > 0:
        url = args[0]
        image = vision.Image()
        image.source.image_uri = url
        response = client.label_detection(image=image)
    else:
        content = await message.attachments[0].read()
        image = vision.Image(content=content)
        response = client.label_detection(image=image)
    labels = response.label_annotations
    output = ", ".join([label.description + " (score: " + str(label.score)[:4] + ")" for label in labels])
    return await message.channel.send(output)       



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
