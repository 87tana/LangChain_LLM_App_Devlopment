# -*- coding: utf-8 -*-
"""Tagging_Extraction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MjjsLdOCeGDKaXAUn3rlnrIieGZKa5E-

## Tagging and Extraction Using OpenAI functions
"""

from google.colab import drive
drive.mount('/content/drive/', force_remount=True)

openai_api_key =

from typing import List # help with type hints
from pydantic import BaseModel, Field #pydantic data validation
from langchain.utils.openai_functions import convert_pydantic_to_openai_function # Converts the Pydantic schema into a format OpenAI's function calling can use.

class Tagging(BaseModel): # A class and a list of attributes
    """Tag the piece of text with particular info."""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")  # this is what we want LLM extract
    language: str = Field(description="language of text (should be ISO 639-1 code)")

convert_pydantic_to_openai_function(Tagging)  # use openai function methods on this class (tagging)

!pip install langchain-community langchain-core --quiet

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

model = ChatOpenAI(temperature = 0,openai_api_key = openai_api_key)

tagging_functions = [convert_pydantic_to_openai_function(Tagging)]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Think carefully, and then tag the text as instructed"),
    ("user", "{input}")
])

model_with_functions = model.bind(
    functions = tagging_functions,
    function_call = {"name": "Tagging"}
)

tagging_chain = prompt | model_with_functions

tagging_chain.invoke({"input": "I love langchain"})

tagging_chain.invoke({"input": "non mi piace questo cibo"})

from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

tagging_chain = prompt | model_with_functions | JsonOutputFunctionsParser()

tagging_chain.invoke({"input": "non mi piace questo cibo"})

tagging_chain.invoke({"input": "Du siehst müde aus"})

"""## Extraction

- Extraction is similar to tagging, but used for extracting multiple pieces of information.

"""

from typing import Optional   # pydantic model, that represent structured info.
class Person(BaseModel):  # define piece of information we wanna extract
    """Information about a person."""
    name: str = Field(description="person's name")
    age: Optional[int] = Field(description="person's age")

class Information(BaseModel):  # extract a list of objects
    """Information to extract."""
    people: List[Person] = Field(description="List of info about people")

convert_pydantic_to_openai_function(Information) # this information class is then passing to openAI function

extraction_functions = [convert_pydantic_to_openai_function(Information)] # extraction function
extraction_model = model.bind(functions = extraction_functions, function_call={"name": "Information"}) #set up extraction model

extraction_model.invoke("Joe is 30, his mom is Martha")

"""- now want to force model to response more educated way"""

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the relevant information, if not explicitly provided do not guess. Extract partial info"),
    ("human", "{input}")
])

extraction_chain = prompt | extraction_model

extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})

extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()

extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})

"""## try different output parser"""

from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser # look for particular key and only extract that

extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="people")

extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})

"""# Doing it for real

- We can apply tagging to a larger body of text.

- For example, let's load this blog post and extract tag information from a sub-set of the text.

"""

from langchain.document_loaders import WebBaseLoader # load doc

loader = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/")
documents = loader.load()

doc = documents[0]

page_content = doc.page_content[:10000] # get the first 10.000 charcters

print(page_content[:1000])

"""- now we are going some tagging and extraction."""

class Overview(BaseModel):  # first we create a class, describe what we wanna to TAG
    """Overview of a section of text.""" # overview of this artcle --> like a prompt
    summary: str = Field(description="Provide a concise summary of the content.") # extract summary
    language: str = Field(description="Provide the language that the content is written in.") # extract language
    keywords: str = Field(description="Provide keywords related to the content.") # any keywords

overview_tagging_function = [  # set a chain
    convert_pydantic_to_openai_function(Overview)  # convert pydantic to openAI
]
tagging_model = model.bind(
    functions = overview_tagging_function,
    function_call = {"name":"Overview"}
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()

tagging_chain.invoke({"input": page_content})

class Paper(BaseModel): # create base model here
    """Information about papers mentioned."""
    title: str #title
    author: Optional[str] #author


class Info(BaseModel):  # put inside another class --> "info" we want create a list of paper
    """Information to extract"""
    papers: List[Paper]

paper_extraction_function = [  # convert pydantic to openAI
    convert_pydantic_to_openai_function(Info)
]
extraction_model = model.bind(
    functions= paper_extraction_function,
    function_call= {"name":"Info"}
)
extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")

extraction_chain.invoke({"input": page_content})

"""- it'S not accurate return so we need a accurate  promot"""

template = """A article will be passed to you. Extract from it all papers that are mentioned by this article follow by its author.

Do not extract the name of the article itself. If no papers are mentioned that's fine - you don't need to extract any! Just return an empty list.

Do not make up or guess ANY extra information. Only extract what exactly is in the text."""

prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    ("human", "{input}")
])

extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")

extraction_chain.invoke({"input": page_content})

extraction_chain.invoke({"input": "hi"}) # chexk in order to see follow the prompt

"""-so far it as 10.000 charcters of the article,what about extracting the whole articles"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_overlap=0)

"""- why need to chunk? the article is too long. and if we pass the whole artcle into LLM, it will be too big for token window.

- we are gonna pass all the token individually and then combine all at the end
"""

splits = text_splitter.split_text(doc.page_content)

len(splits)

"""- now we are going to create the entire chain, using LangChain Expression Language (LCEL) that does everything:

- taking the page content
- spilit it into chunk
- pass those individual chunk into extraction chain
- join all the results together.

- we need to create a function that can join list of lists and flatten them.
"""

def flatten(matrix):  # create a function that can join list of lists and flatten them.
    flat_list = []   # extract and merge them all.
    for row in matrix:
        flat_list += row
    return flat_list

flatten([[1, 2], [3, 4]])

"""- we need a way to preparing methods that pass the  spilit into chain
- we need to convert a list of text to a list of doctionary.
"""

print(splits[0])

from langchain.schema.runnable import RunnableLambda # simple wrapper in langchain.

"""- Input: A single string (your document).

- Action: Split the string into smaller chunks using text_splitter.

- Output: A list of dictionaries, each like {"input": chunk}.
"""

prep = RunnableLambda(
    lambda x: [{"input": doc} for doc in text_splitter.split_text(x)]
)

prep.invoke("hi")

chain = prep | extraction_chain.map() | flatten  # because we have a list of elements we use .map()

"""- take a list of elemts --> prep
- map the chain overthem
- flatten -> because we have a list of list

- first spilit into 15 sections  --> prep
- pass into the extraction chains  --> extract_chain.map()
- parallize a lot of call automatically
- finall call --> flatten
"""

chain.invoke(doc.page_content)