"""AI scene planner. Runs outside the UI thread; credentials stay in the environment."""
import json
import os
import urllib.request

def plan_scene(prompt,roster):
    provider=os.getenv('FOOTBALL_AI_PROVIDER','ollama')
    model=os.getenv('FOOTBALL_AI_MODEL','llama3.2' if provider=='ollama' else 'gpt-4.1-mini')
    system=('You direct a football manhwa match. Return only a JSON object with player, action, method, commentary. '
            'action must be Goal, Save, Miss, or Pass. method must be header, free kick, long shot, or dribble and finish. '
            'player must be an exact on-pitch player name from this roster: '+', '.join(roster)+
            '. Honor the requested outcome. Commentary must describe how the action happens in at most 180 characters.')
    if provider=='ollama':
        url='http://localhost:11434/api/chat'
        body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'stream':False,'format':'json'}
        headers={'Content-Type':'application/json'}
    elif provider=='openai':
        key=os.getenv('FOOTBALL_AI_KEY')
        if not key: raise ValueError('Set FOOTBALL_AI_KEY securely before using OpenAI.')
        url='https://api.openai.com/v1/chat/completions'
        body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'response_format':{'type':'json_object'}}
        headers={'Content-Type':'application/json','Authorization':'Bearer '+key}
    else: raise ValueError('FOOTBALL_AI_PROVIDER must be ollama or openai.')
    request=urllib.request.Request(url,data=json.dumps(body).encode(),headers=headers)
    try:
        with urllib.request.urlopen(request,timeout=40) as response:
            result=json.load(response)
    except Exception as error:
        raise ValueError('AI connection failed. Check provider, model and credentials.') from error
    content=result['message']['content'] if provider=='ollama' else result['choices'][0]['message']['content']
    scene=json.loads(content)
    if scene.get('player') not in roster or scene.get('action') not in ('Goal','Save','Miss','Pass'):
        raise ValueError('AI returned an invalid player or action. No match changes applied.')
    if scene.get('method') not in ('header','free kick','long shot','dribble and finish'):
        raise ValueError('AI returned an unsupported scoring method.')
    if not isinstance(scene.get('commentary'),str) or not scene['commentary'].strip():
        raise ValueError('AI returned empty commentary.')
    return scene
