from hailo_toolbox import create_source
from hailo_toolbox.models import ModelsZoo
import numpy as np

if __name__ == "__main__":
    source = create_source(
        "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example.mp4"
    )

    # Load ArcFace MobileNet face recognition model
    inference = ModelsZoo.face_recognition.arcface_r50()

    for img in source:
        results = inference.predict(img)
        for result in results:
            embeddings = result.get_embeddings()

            print(f"Face Recognition Result:")
            print(f"  Feature vector shape: {embeddings.shape}")
            print(f"  Feature vector dimension: {embeddings.shape[-1]}")
            print(f"  Feature vector norm: {np.linalg.norm(embeddings):.3f}")
            print(
                f"  Feature vector range: [{embeddings.min():.3f}, {embeddings.max():.3f}]"
            )
            print("---")
