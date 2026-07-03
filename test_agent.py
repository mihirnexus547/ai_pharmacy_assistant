from services.agent import agent

response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Do you have Crocin?"
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "test_session",
        }
    }
)

print(response["messages"][-1].content)