# Frontend Integration Notes

## API Response Schema
The backend uses **snake_case** for all JSON fields. 
Please ensure your frontend Types/Interfaces match this convention.

### Example: Login Response
```json
{
  "access_token": "...",  // NOT accessToken
  "token_type": "bearer", // NOT tokenType
  "full_name": "...",     // NOT fullName
  "expires_at": "..."     // NOT expiresAt
}
```

### Example: History Item
```json
{
  "session_id": 123,      // NOT glueSessionId
  "room_code": "ABC",     // NOT roomCode
  "total_score": 85.5     // NOT totalScore
}
```
