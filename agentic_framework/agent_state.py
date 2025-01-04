from typing import TypedDict, Annotated, List
from typing import TypedDict, Annotated
import operator


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
    addSqliteDB: bool
    bankInfo: List[str]