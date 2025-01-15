from langgraph.checkpoint.sqlite import SqliteSaver
from agentic_framework.invoice_agent import InvoiceAgent
from agentic_framework.agent_tools import add_task_api_directly, update_sqlitedb_then_task_api
from agentic_framework.agent_state import InvoiceAgentState
from sqlalchemy.orm import sessionmaker

import sys
parent_dir = ".."
sys.path.append(parent_dir)
import models.base

def run(session):
    tools = [add_task_api_directly, update_sqlitedb_then_task_api]
    initial_state = InvoiceAgentState()
    initial_state['invoices_dict'] = [None]
    initial_state['invoices_text'] = [None]
    memory = SqliteSaver.from_conn_string(":memory:")
    agent = InvoiceAgent(tools, checkpointer = None, session=session, system='')
    result = agent.graph.invoke(initial_state)
    print(result)

if __name__ == '__main__':

    Session = sessionmaker(bind=models.base.engine)
    session = Session()
    run(session)