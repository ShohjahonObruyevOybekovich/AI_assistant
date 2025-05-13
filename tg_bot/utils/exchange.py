import httpx

async def get_exchange_rates():
    url = "https://cbu.uz/oz/arkhiv-kursov-valyut/json/"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            rates = response.json()
    except Exception as e:
        return None, str(e)

    return {
        item["Ccy"]: float(item["Rate"].replace(",", ""))
        for item in rates
    }, None