"""
This file registers the model with the Python SDK.
"""

from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.services.vision import VisionClient

from .verificationclassifier import VerificationSystem

Registry.register_resource_creator(
    VisionClient.API,
    VerificationSystem.MODEL,
    ResourceCreatorRegistration(VerificationSystem.new, VerificationSystem.validate),
)
