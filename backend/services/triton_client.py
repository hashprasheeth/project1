import numpy as np
import cv2
import tritonclient.grpc as grpcclient
from tritonclient.utils import InferenceServerException
from fastapi import HTTPException
from backend.core.config import settings
from backend.core.logger import logger

class TritonClient:
    def __init__(self):
        self.url = settings.TRITON_GRPC_URL
        self.client = None
        
    def connect(self):
        if not self.client:
            try:
                self.client = grpcclient.InferenceServerClient(url=self.url)
            except Exception as e:
                logger.error("triton_connection_failed", extra={"error": str(e), "url": self.url})
                raise HTTPException(status_code=503, detail="Triton Inference Server Unavailable")

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image")
                
            # Resize
            img_resized = cv2.resize(img, (1280, 1280))
            
            # Normalize/Format (NHWC -> NCHW, etc as per model need)
            img_input = img_resized.astype(np.float32)
            img_input = np.expand_dims(img_input, axis=0)
            img_input = np.transpose(img_input, (0, 3, 1, 2))
            
            return img_input
        except Exception as e:
            logger.error("preprocess_failed", extra={"error": str(e)})
            raise HTTPException(status_code=400, detail="Invalid image format")

    def infer(self, image_bytes: bytes):
        self.connect()
        
        input_data = self.preprocess(image_bytes)
        
        inputs = []
        inputs.append(grpcclient.InferInput("input_tensor", input_data.shape, "FP32"))
        inputs[0].set_data_from_numpy(input_data)
        
        outputs = []
        outputs.append(grpcclient.InferRequestedOutput("output_tensor"))
        
        try:
            results = self.client.infer(model_name=settings.MODEL_NAME, inputs=inputs, outputs=outputs)
            return results.as_numpy("output_tensor")
        except InferenceServerException as e:
            logger.error("inference_failed", extra={"error": str(e), "model": settings.MODEL_NAME})
            raise HTTPException(status_code=500, detail="Model Inference Failed")
        except Exception as e:
            logger.error("rpc_failed", extra={"error": str(e)})
            raise HTTPException(status_code=503, detail="Upstream RPC Error")
            
    def is_healthy(self) -> bool:
        try:
            self.connect()
            return self.client.is_server_live()
        except:
            return False

triton_svc = TritonClient()
