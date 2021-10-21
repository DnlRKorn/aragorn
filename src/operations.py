async def sort_results_score(message,params,guid):
    results = message['message']['results']
    aord = params.get('ascending_or_descending','descending')
    reverse = (aord=='descending')
    try:
        message['message']['results'] = sorted(results,key=lambda x: x.get('score',0),reverse=reverse)
    except KeyError:
        #can't find the right structure of message
        return message,400
    return message,200

async def filter_results_top_n(message,params,guid):
    #It's a validation error to not include max_results as a parameter, but let's have a default
    n = params.get('max_results',20000)
    try:
        message['message']['results'] = message['message']['results'][:n]
    except KeyError:
        #not a 'mesage' or 'results'
        return message,400
    return message,200

async def filter_kgraph_orphans(message,params,guid):
    """Remove from the knowledge graph any nodes and edges not references by a result"""
    #First, find all the result nodes and edges
    results = message.get('message',{}).get('results',[])
    nodes = set()
    edges = set()
    for result in results:
        for qnode,knodes in result.get('node_bindings',{}).items():
            nodes.update([ k['id'] for k in knodes ])
        for qedge, kedges in result.get('edge_bindings', {}).items():
            edges.update([k['id'] for k in kedges])
    #now remove all knowledge_graph nodes and edges that are not in our nodes and edges sets.
    kg_nodes = message.get('message',{}).get('knowledge_graph',{}).get('nodes',{})
    message['message']['knowledge_graph']['nodes'] = { nid: ndata for nid, ndata in kg_nodes.items() if nid in nodes }
    kg_edges = message.get('message',{}).get('knowledge_graph',{}).get('edges',{})
    message['message']['knowledge_graph']['edges'] = { eid: edata for eid, edata in kg_edges.items() if eid in edges }
    return message,200

async def filter_message_top_n(message,params,guid):
    """Aggregator for sort_results_score, filter_results_top_n, filter_kgraph_orphans.
    Aggregating these allows us to skip (potentially expensive) filter_kgraph_orphans if no filtering is done on the results."""
    n = params.get('max_results', 20000)
    sortedmessage, status = await sort_results_score(message,params,guid)
    num_results = len(sortedmessage.get('message',{}).get('results',[]))
    if num_results > n:
        fmessage, status = await filter_results_top_n(sortedmessage,params,guid)
        rmessage, status = await filter_kgraph_orphans(fmessage,params,guid)
        return rmessage,status
    else:
        return sortedmessage,status

