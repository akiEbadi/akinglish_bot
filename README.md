# akinglish_bot
longman and oxford dictionary

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt


ngrok http 8000
Forwarding: https://5a11-37-27-220-205.ngrok-free.app -> http

https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook?url={ngrok}/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/webhook7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ


ngrok http 8000
answer: https://2e31-162-55-220-162.ngrok-free.app

https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook?url=https://2e31-162-55-220-162.ngrok-free.app/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ

{"ok":true,"result":true,"description":"Webhook was set"}
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload


curl -X POST "https://api.telegram.org/bot7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ/setWebhook?url=https://2e31-162-55-220-162.ngrok-free.app/webhook/7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ"


