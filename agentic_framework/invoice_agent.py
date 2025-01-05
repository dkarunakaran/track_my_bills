from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_ollama import ChatOllama
import yaml
from agent_state import InvoiceAgentState
from langchain.agents import Tool
from langchain.tools import BaseTool
import random
from agent_nodes import get_emails_invoice_node
import sqlitedb
import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility



memory = SqliteSaver.from_conn_string(":memory:")
# download = Download()
# generate = Generate()
# Read and process emails - node 1
# download.get_emails()

# Read and check bank details. This is to make sure the bank details has not been changed - node 2
# If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to node 3

# Read and process drive files - node 3
# download.get_drive_files()

# Read and check bank details. This is to make sure the bank details has not been changed - node 4
# If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to node 5

# Create the Task based on the processed data - node 5
# generate.task_API_operation()

# Ref 1: https://www.analyticsvidhya.com/blog/2024/10/setting-up-custom-tools-and-agents-in-langchain/
# Ref 2: https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/3/langgraph-components
# Ref 3: https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/7/essay-writer
# Ref 4: https://medium.com/@lorevanoudenhove/how-to-build-ai-agents-with-langgraph-a-step-by-step-guide-5d84d9c7e832

with open("/app/config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

def meaning_of_life(input=""):
    return 'The meaning of life is 42 if rounded but is actually 42.17658'

life_tool = Tool(
    name='Meaning of Life',
    func= meaning_of_life,
    description="Useful for when you need to answer questions about the meaning of life. input should be MOL "
)

def random_num(input=""):
    return random.randint(0,5)

random_tool = Tool(
    name='Random number',
    func= random_num,
    description="Useful for when you need to get a random number. input should be 'random'"
)

class InvoiceAgent:
    def __init__(self, model, tools, system=""):
        # Creating databse if not existed
        utility.create_database()

        self.system = system
        graph = StateGraph(InvoiceAgentState)
        graph.add_node("email-invoices", self.get_email_invoice)
        graph.add_node("drive-invoices", self.get_drive_invoice)
        graph.add_node("add-sqlitedb", self.add_to_sqlite_db)
        graph.add_node("extract-bank-info", self.extract_bank_info)
        graph.add_node("llm", self.call_llm)
        graph.add_node("take_action", self.take_action)
        graph.set_entry_point("email-invoices")
        graph.add_edge("email-invoices", "drive-invoices") 
        graph.add_edge("drive-invoices", "add-sqlitedb") 
        graph.add_edge("add-sqlitedb", "extract-bank-info") 
        graph.add_edge("extract-bank-info", "llm") 
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "take_action", False: END}
        )
        graph.add_edge("take_action", END)
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def get_email_invoice(self, state: InvoiceAgentState):
        
        get_emails_invoice_node()
        
        return {'invoices': ["hi1"]}

    def get_drive_invoice(self, state: InvoiceAgentState):

        return {'invoices': ["hi2"]}
    
    def add_to_sqlite_db(self, state: InvoiceAgentState):

        return {'add_sqlite_DB': True}
    
    def extract_bank_info(self, state: InvoiceAgentState):

        return {'bank_info': ['sdds','fgfg']}
    
    def call_llm(self, state: InvoiceAgentState):
        # Compare the data to decide which tool to use
        messages = [SystemMessage(content=cfg['invoice_agent']['prompt_for_API_tools']),"What is the meaning of life?"]
        message = self.model.invoke(messages)
        
        return {'llm_msg': message}

    def exists_action(self, state: InvoiceAgentState):
        result = state['llm_msg']
        return len(result.tool_calls) > 0
    
    def take_action (self, state: InvoiceAgentState):
        tool_calls = state['llm_msg'].tool_calls
        results = []
    
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
    
        return {'api_operation': results}

if __name__ == "__main__":
    model = ChatOllama(model=cfg['invoice_agent']['model_for_API_tool'], base_url=cfg['invoice_agent']['host'])
    tools = [random_tool, life_tool]
    initial_state = InvoiceAgentState()
    initial_state['invoices'] = ['None']
    agent = InvoiceAgent(model, tools, system='')
    result = agent.graph.invoke(initial_state)
    print(result)



