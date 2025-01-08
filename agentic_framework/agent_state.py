from typing import TypedDict, Annotated, List
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage


class InvoiceAgentState(TypedDict):
    invoices_dict: Annotated[List[dict], operator.add]
    invoices_text: Annotated[List[str], operator.add]
    add_sqlite_DB: bool
    bank_info: List[dict]
    llm_msg: Annotated[List[str], operator.add]
    #api_operation: list[AnyMessage]
    api_operation: str