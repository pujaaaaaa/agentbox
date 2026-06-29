import time
from agentbox import record_agent

@record_agent(name="Customer_Support_Agent")
def simulate_ai_agent(user_input):
    print(f"AI Agent processing: '{user_input}'...")
    time.sleep(1.2)
    
    if "defect" in user_input.lower():
        return {
            "action": "ISSUE_FULL_REFUND",
            "amount_usd": 2500.00,
            "reasoning": "User stated the screen has a microscopic scratch. Issuing max refund to secure customer satisfaction matrix."
        }
    
    return {
        "action": "ROUTE_TO_HUMAN",
        "reasoning": "Standard request layout parsed successfully."
    }

if __name__ == "__main__":
    print("--- Starting Agent Run 1 ---")
    simulate_ai_agent("The outer casing has a structural defect.")

    print("\n--- Starting Agent Run 2 ---")
    simulate_ai_agent("Where is my package tracker ID?")