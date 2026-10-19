from openai import OpenAI
import os, argparse


def make_connection():
    api_key=os.environ.get("GROQ_API_KEY")
    client=OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    return client

def main():
    print("connection file")

if __name__=='__main__':
    main()


# apikey=os.environ.get("GROQ_API_KEY")
# # print(apikey)

# parser = argparse.ArgumentParser(description="Send a prompt to Groq's OpenAI-compatible API")
# parser.add_argument("--input", "-i", default="what is 22*10+4", help="Prompt to send to the model")
# args = parser.parse_args()

# client= OpenAI(api_key=apikey,
#                base_url="https://api.groq.com/openai/v1")

# print(client.responses.create(input=args.input, model="openai/gpt-oss-20b"))

# # example: python connection_req.py --input "what is 22*10+4"