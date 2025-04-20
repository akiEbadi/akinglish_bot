# akinglish_bot
longman and oxford dictionary

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt


ngrok http 8000
Forwarding: https://5a11-37-27-220-205.ngrok-free.app -> http

https://api.telegram.org/bot{Token}/setWebhook?url={ngrok}/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/webhook{Token}


ngrok http 8080
answer: https://72d7-37-27-220-205.ngrok-free.app

https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook?url=https://72d7-37-27-220-205.ngrok-free.app/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ

{"ok":true,"result":true,"description":"Webhook was set"}
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload




curl -X POST "https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook?url=https://2e31-162-55-220-162.ngrok-free.app/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ"

curl -F "url=https://akinglishbot-production.up.railway.app/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ" https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook



development:
@akinglish_dev_bot
ngrok http 5000

curl -X POST "https://api.telegram.org/bot8080464719:AAHnt8AeKm1zumOnERZzRfw40J49vB3aHqo/setWebhook?url=https://785e-37-27-220-205.ngrok-free.app/webhook/8080464719:AAHnt8AeKm1zumOnERZzRfw40J49vB3aHqo"

https://api.telegram.org/bot8080464719:AAHnt8AeKm1zumOnERZzRfw40J49vB3aHqo/getWebhookInfo

uvicorn main:app --host 0.0.0.0 --port 5000 --reload

curl -F "url=https://785e-37-27-220-205.ngrok-free.app/webhook/8080464719:AAHnt8AeKm1zumOnERZzRfw40J49vB3aHqo" https://api.telegram.org/bot8080464719:AAHnt8AeKm1zumOnERZzRfw40J49vB3aHqo/setWebhook
