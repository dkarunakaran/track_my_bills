from typing import TypedDict, Annotated, List
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage


class InvoiceAgentState(TypedDict):
    #task: str
    #plan: str
    #draft: str
    #critique: str
    #content: List[str]
    #revision_number: int
    #max_revisions: int
    #email: List[str]
    invoices: Annotated[List[str], operator.add]
    add_sqlite_DB: bool
    bank_info: List[str]
    llm_msg: str
    #api_operation: list[AnyMessage]
    api_operation: str