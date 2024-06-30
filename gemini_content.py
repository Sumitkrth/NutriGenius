import os
import requests
api_key = os.getenv("GOOGLE_API_KEY")

def parse_function_response(message):
    function_call = message.get("functionCall")
    if function_call:
        function_name = function_call.get("name")
        print("Gemini: call function ", function_name)
        try:
            arguments = function_call.get("args",)
            print("Gemini: arguments are ", arguments)
            if arguments:
                # Replace this with the actual function implementation if needed
                function_response = "Function call detected, but no function to execute"
            else:
                function_response = "No arguments are present"
        except Exception as e:
            print(e)
            function_response = "Invalid Function"
        return function_response
    return None

def run_conversation(user_message):
    messages = []

    system_message = '''You are an AI chatbot with extensive knowledge and expertise in the field
    of nutrition and diet, with a decade of experience in this domain. When asked to provide information
    or assistance, respond in a manner that conveys the authority and confidence of a healthcare professional.
    Utilize the function call feature when necessary and ensure your responses are informative and helpful.'''

    message = {
        "role": "user",
        "parts": [{"text": system_message + "\n" + user_message}]
    }
    messages.append(message)

    data = {
        "contents": messages,
    }

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key
    response = requests.post(url, json=data)

    if response.status_code != 200:
        print(response.text)
        return

    t1 = response.json()
    candidate = t1.get("candidates", [{}])[0]
    content = candidate.get("content", {})
    parts = content.get("parts", [])
    if not parts:
        print("Error: No content in response")
        return

    message_text = parts[0].get("text", "")
    print("message ###############:", message_text)

    if 'functionCall' in content:
        resp1 = parse_function_response(content)
        return resp1
    else:
        print("no function call")
        return message_text

if __name__ == "__main__":
    user_message = input("how can I help you?\n")
    print(run_conversation(user_message))


