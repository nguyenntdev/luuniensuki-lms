# AI Teacher Agent

Thu muc nay co 2 module:

1. `realtime_worker.py`: worker doc-lap, xu ly su kien `ai_voice_request` cho phong live.
2. `mock_agent.py`: script local de test prompt/policy (khong dung trong production).

## Chay worker realtime

```bash
python services/ai_teacher_agent/realtime_worker.py --interval 1.0 --log-level INFO
```

Worker se:
- Tu dam bao AI Teacher co mat trong roster participant cua session live.
- Nhan event `ai_voice_request` tu `live_events`.
- Goi DeepSeek (neu co key), neu loi thi fallback `hint-first` theo policy su pham.
- Ghi event `ai_transcript_chunk` + `ai_voice_ready` de frontend doc va phat TTS.

## Chay script local (legacy)

```bash
python services/ai_teacher_agent/mock_agent.py
```
