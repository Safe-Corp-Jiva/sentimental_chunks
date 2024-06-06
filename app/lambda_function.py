import openai, json, os

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')

if not API_URL or not API_KEY:
  raise Exception('API_URL and API_KEY must be set in the environment')

chunksQuery = gql("""
query ChunksByCallId($callId: ID!) {
  chunksByCallId(callId: $callId) {
    items {
      id
      sentiment
      callId
      createdAt
      updatedAt
      content {
        role
        text
      }
    }
  }
}
""")

callUpdate = gql("""
  mutation UpdateCall($id: ID!, $result: CallResult!) {
    updateCall(
      input: {id: $id, result: $result}
    ) {
      id
      createdAt
      status
      help
      result
      updatedAt
      callCallerId
      agent {
        id
        username
        lastName
        firstName
        email
      }
      queue {
        id
        name
      }
      topic {
        id
        name
        count
      }
      metrics {
        id
        length
        waittime
      }
    }
  }"""
)

transport = RequestsHTTPTransport(
  url=API_URL,
  headers={'x-api-key': API_KEY}
)

client = Client(transport=transport, fetch_schema_from_transport=True)

def handler(event, context):
    callId = event.get('callId')

    if not callId:
      body = event.get('body')
      if body:
        try:
          body = json.loads(body)
          callId = body.get('callId')
        except:
          return {
            'statusCode': 400,
            'body': json.dumps('Failed to parse body')
          }

    if not callId:
      return {
        'statusCode': 400,
        'body': json.dumps('No callId found')
      }

    data = client.execute(
       chunksQuery, 
       variable_values={'callId': callId}
    ).get('chunksByCallId', {}).get('items', [])
        

    def parser(data):  
      return [i['content'] for i in data]

    def guesser(data):
      xq = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
          {"role": "system", "content": "You are a helpful assistant that ranks conversations between a CUSTOMER and an AGENT. You can only rank it: SATISFIED, NEUTRAL, UNSATISFIED. Answer only with one of these options."},
          {"role": "user", "content": f"{data}"},
        ],
      )
      result = xq.choices[0].message.content
      print("Result: ", result)
      if result in ['SATISFIED', 'NEUTRAL', 'UNSATISFIED']:
        return result
      else:
        return 'NEUTRAL'

    if not data:
      return {
        'statusCode': 400,
        'body': json.dumps('No data found')
      }
    
    rank = guesser(parser(data))

    if rank:
      final = client.execute(
        callUpdate, 
        variable_values={'id': callId, 'result': rank}
      ).get('updateCall', {})

      if not final:
        return {
          'statusCode': 400,
          'body': json.dumps('No data returned from gql')
        }
      
      return {
        'statusCode': 200,
        'body': json.dumps(final)
      }
  
    else:
      return {
        'statusCode': 400,
        'body': json.dumps('Failed to rank call')
      }