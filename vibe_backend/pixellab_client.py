import httpx

PIXELLAB_BASE_URL = "https://api.pixellab.ai/v1"


async def generate_image(prompt: str, key: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{PIXELLAB_BASE_URL}/generate-image",
            headers={"Authorization": f"Bearer {key}"},
            json={"prompt": prompt, "output_format": "png"},
        )
        response.raise_for_status()
        data = response.json()
        # PixelLab returns base64-encoded image in data.image or data.images[0]
        import base64
        img_b64 = data.get("image") or data.get("images", [None])[0]
        if img_b64 is None:
            raise ValueError(f"Unexpected PixelLab response: {data}")
        return base64.b64decode(img_b64)


async def modify_image(prompt: str, image_b64: str, key: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{PIXELLAB_BASE_URL}/edit-image",
            headers={"Authorization": f"Bearer {key}"},
            json={"prompt": prompt, "image": image_b64, "output_format": "png"},
        )
        response.raise_for_status()
        data = response.json()
        import base64
        img_b64 = data.get("image") or data.get("images", [None])[0]
        if img_b64 is None:
            raise ValueError(f"Unexpected PixelLab response: {data}")
        return base64.b64decode(img_b64)
