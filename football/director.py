"""Local story commands. No external AI or credentials are used."""
import re

def direct(match, text):
    if match.finished:
        return 'Start a new match before directing another scene.'
    text = text.strip()
    if not text:
        return 'Write a scene first.'
    lower = text.lower()
    found = [(s,i,p) for s,t in enumerate(match.teams) for i,p in enumerate(t.players)
             if re.search(r'\b'+re.escape(p.name.lower())+r'\b',lower)]
    if not found:
        return 'Include an on-pitch player name, for example: Akira scores a header.'
    side,index,player = found[0]
    kinds = [('Goal',r'\b(score|scores|scored|goal)\b'),
             ('Save',r'\b(save|saves|saved)\b'),
             ('Miss',r'\b(miss|misses|missed)\b'),
             ('Pass',r'\b(pass|passes|passed)\b')]
    kind = next((k for k,pattern in kinds if re.search(pattern,lower)),None)
    if not kind:
        return 'Supported scenes: scores, saves, misses, or passes. Include a player name.'
    if kind == 'Save' and player.role == 'GK':
        side=1-side
        index=9
        player=match.teams[side].players[index]
    match.owner=side; match.carrier=index
    if kind in ('Goal','Save','Miss'):
        stats=match.stats[side]; stats['shots']+=1; stats['xg']+=.35
        if kind!='Miss': stats['on_target']+=1
    if kind=='Goal': match.score[side]+=1
    method = 'header' if 'header' in lower else 'free kick' if 'free kick' in lower else 'long shot' if 'long' in lower else 'dribble and finish'
    match.event(kind,side,text,player=player.name,source='director',method=method,
                team_side=side,scorer_index=index,goal_path=goal_path(side,index,method))
    return 'Scene applied: '+text

def goal_path(side,index,method):
    # Coordinates follow the attacking direction, with a buildup and finish.
    points = [[.48,.65],[.68,.42],[.84,.48],[1.,.5]]
    if method=='header': points=[[.60,.85],[.83,.72],[.88,.50],[1.,.48]]
    elif method=='free kick': points=[[.74,.32],[.82,.28],[.94,.36],[1.,.47]]
    elif method=='long shot': points=[[.52,.5],[.63,.44],[.83,.47],[1.,.51]]
    return [[1-x if side else x,y] for x,y in points]
