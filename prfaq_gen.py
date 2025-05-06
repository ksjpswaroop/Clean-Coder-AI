import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Define your base URL, token, and headers
base_url = "https://47d568h3nisp5o-8080.proxy.runpod.net/ollama/"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgyZmQzYWY2LTZmMmEtNDM0OC1iMjM5LWYwNmFhMjM5ZjNjZiJ9.HxP9_iYKozTssdMvHq3F7nBNfC33RZV8OoAO0aHedxY"
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Initialize the ChatOllama model with streaming enabled.
model = ChatOllama(
    model="mathzenepoch1",
    model_provider="ollama",
    temperature=0,
    max_tokens=1000,
    base_url=base_url,
    streaming=True,
    client_kwargs={"headers": headers},
    headers=headers,
)

# Create a chat prompt template that includes a placeholder for history.
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Build the LLMChain.
chain = LLMChain(llm=model, prompt=chat_prompt)

# Custom callback handler that replaces <think> tokens with <reasoning>.
class CustomStreamingCallbackHandler(StreamingStdOutCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if token == '<think>':
            token = "<reasoning>"
        elif token == '</think>':
            token = "</reasoning>"
        print(token, end="", flush=True)

# Define your input.
input_text = "write a function for reversing a string"

# Supply both 'input' and 'history' keys.
chain_inputs = {"input": input_text, "history": []}

# Run the chain with the custom streaming callback using .invoke()
chain.invoke(chain_inputs, callbacks=[CustomStreamingCallbackHandler()])