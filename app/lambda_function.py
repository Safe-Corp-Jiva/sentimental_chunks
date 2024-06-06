import boto3, openai, json, os


def lambda_handler(event, context):
    data = event['data']
    
    OPENAI_API_KEY=os.environ["OPENAI_API_KEY"]

    def parser(data):   
        data = data[0]['chunks']['items']
        data = [i['content'] for i in data]

        return data

    def guesser(data):
        xq = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that ranks conversations between a CUSTOMER and an AGENT. You can only rank it: SATISFIED, NEUTRAL, UNSATISFIED"},
                {"role": "user", "content": f"{data}"},
            ],
        )
        return xq.choices[0].message.content

    rank = guesser(parser(data))

    if rank:
        return {
            'statusCode': 200,
            'body': json.dumps(rank)
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Error')
        }