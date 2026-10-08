"""SIGNAL data model — full TRD §3 table set.

Importing this package registers every model on `Base.metadata`.
"""

from app.models.audit_log import AuditLogEntry
from app.models.child import Child
from app.models.flag import Flag
from app.models.institution import Institution
from app.models.knowledge_review import KnowledgeReviewNote
from app.models.knowledge_release import KnowledgeRelease
from app.models.knowledge_revision import KnowledgeRevision
from app.models.milestone import Milestone
from app.models.observation import Observation
from app.models.provider_credential import ProviderCredential
from app.models.referral import Referral
from app.models.safeguarding_escalation import SafeguardingEscalation
from app.models.session import Session
from app.models.staff import Staff
from app.models.usage_log import UsageLog

__all__ = [
    "AuditLogEntry",
    "Child",
    "Flag",
    "Institution",
    "KnowledgeReviewNote",
    "KnowledgeRelease",
    "KnowledgeRevision",
    "Milestone",
    "Observation",
    "ProviderCredential",
    "Referral",
    "SafeguardingEscalation",
    "Session",
    "Staff",
    "UsageLog",
]
