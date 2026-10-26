import asyncio

from viam.module.module import Module
from viam.services.vision import VisionClient

from .verificationclassifier import VerificationSystem


async def main():
    module = Module.from_args()
    module.add_model_from_registry(VisionClient.API, VerificationSystem.MODEL)
    await module.start()


if __name__ == "__main__":
    asyncio.run(main())
