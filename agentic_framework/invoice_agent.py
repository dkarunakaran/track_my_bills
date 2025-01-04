from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain_ollama import ChatOllama
import yaml
from agent_state import InvoiceAgentState

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

class InvoiceAgent:
    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(InvoiceAgentState)
        graph.add_node("email-invoices", self.get_email_invoice)
        graph.add_node("drive-invoices", self.get_drive_invoice)
        graph.add_node("add-sqlitedb", self.add_to_sqlite_db)
        graph.add_node("extract-bank-info", self.extract_bank_info)
        graph.set_entry_point("email-invoices")
        graph.add_edge("email-invoices", "drive-invoices") 
        graph.add_edge("drive-invoices", "add-sqlitedb") 
        graph.add_edge("add-sqlitedb", "extract-bank-info") 
        self.graph = graph.compile()
        print(self.graph)

    def get_email_invoice(self, state: InvoiceAgentState)->List[str]:
        
        return {'invoices': ["hi1"]}

    def get_drive_invoice(self, state: InvoiceAgentState)->List[str]:

        return {'invoices': ["hi2"]}
    
    def add_to_sqlite_db(self, state: InvoiceAgentState):

        return {'addSqliteDB': True}
    
    def extract_bank_info(self, state: InvoiceAgentState):

        return {'bankInfo': ['sdds','fgfg']}




if __name__ == "__main__":
    model = ChatOllama(model="llama3.1:8b", base_url=cfg['ollama']['host'])
    tool = None
    initial_state = InvoiceAgentState()
    initial_state['invoices'] = ['None']
    agent = InvoiceAgent(model, [tool])
    result = agent.graph.invoke(initial_state)
    print(result)



