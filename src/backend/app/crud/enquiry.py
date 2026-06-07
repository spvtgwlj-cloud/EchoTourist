"""Enquiry 咨询表单数据访问操作。"""

from app.crud.base import CRUDBase
from app.models.enquiry import Enquiry


crud_enquiry = CRUDBase(Enquiry)
