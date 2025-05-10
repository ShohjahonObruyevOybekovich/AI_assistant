from sqlalchemy.util import await_only


class Debt:
    def __init__(self, user_id: int):
        self.user_id: int = user_id

    async def route(self, data : dict):
        action = data.get('action')

        if action == 'buy':
            return await self.create_debt(data)

        else:
            return "⚠️ Tanlangan qarzdorlik amali mavjud emas."

    async def create_debt(self, data : dict):
        pass