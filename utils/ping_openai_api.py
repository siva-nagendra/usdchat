import http.client
import json
import os

connection = http.client.HTTPSConnection("api.openai.com")

headers = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {os.environ["OPENAI_API_KEY"]}',
}

payload = json.dumps({"model": "gpt-3.5-turbo",
                      "messages": [{"role": "user", "content": "Hello!"}]})

connection.request(
    "POST",
    "/v1/chat/completions",
    body=payload,
    headers=headers)

response = connection.getresponse()
data = response.read()

print(data.decode("utf-8"))
