# -*- coding: utf-8 -*-
"""OpenAIFunctionCalling.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uXbgZfA3y4CAeK4VPGq9s10FInFgApYD
"""

from google.colab import drive
drive.mount('/content/drive/', force_remount=True)

openai_api_key =

import json

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

# define a function
functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]

messages = [
    {
        "role": "user",
        "content": "What's the weather like in Boston?"
    }
]

import openai

# Call the ChatCompletion endpoint

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions
)

print(response)

response_message = response["choices"][0]["message"]

response_message

response_message["content"]

response_message["function_call"]

json.loads(response_message["function_call"]["arguments"])

args = json.loads(response_message["function_call"]["arguments"])

get_current_weather(args)

"""- Pass a message that is not related to a function. --> model is determining whether to use or not use a function."""

messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(

    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
)

print(response)

"""- Pass **additional parameters** to force the model to **use** or **not** a function."""

messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="auto", # by default set to auto --> the language model chosses. to use or not to use
)
print(response)

"""- Use mode 'none' for function call."""

messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="none",
    # another mode for function call is none --> this force the language model not to use any of the functions provided.
)
print(response)

"""- When the message should call a function and still uses mode 'none'
- the message releated to function but we set to none
"""

messages = [
    {
        "role": "user",
        "content": "What's the weather in Boston?",
    }
]

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="none",

)
print(response)

"""- Force calling a function."""

messages = [
    {
        "role": "user",
        "content": "What's the weather like in Boston!",
    }
]

openai.api_key = openai_api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call = {"name": "get_current_weather"},

)
print(response)

messages.append(response["choices"][0]["message"])

args = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
observation = get_current_weather(args)

messages.append(
        {
            "role": "function",
            "name": "get_current_weather",
            "content": observation,
        }
)

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
)
print(response)