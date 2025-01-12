from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import AnyMessage


class InvoiceAgentState(TypedDict):
    invoices_dict: Annotated[List[dict], operator.add]
    invoices_text: Annotated[List[str], operator.add]
    add_sqlite_DB: bool
    bank_info: List[dict]
    llm_msg: Annotated[List[str], operator.add]
    tools: List[str]
    task_api: str


class BankInfoDict(TypedDict):
    details: str
    group_id: int
    type: str
