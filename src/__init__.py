"""
This file registers the model with the Python SDK.
"""

from viam.services.vision import VisionClient
from viam.resource.registry import Registry, ResourceCreatorRegistration

from .verificationclassifier import VerificationSystem

Registry.register_resource_creator(
    VisionClient.SUBTYPE,
    VerificationSystem.MODEL,
    ResourceCreatorRegistration(VerificationSystem.new, VerificationSystem.validate),
)
