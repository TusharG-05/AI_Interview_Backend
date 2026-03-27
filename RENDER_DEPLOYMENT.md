# Render Deployment Environment Configuration

## 🔐 Environment Variables Priority on Render

Render uses the following priority order:
1. **Render Secrets** (highest priority) 
2. **Render Environment Variables**
3. **Docker ENV statements** 
4. **.env file values** (lowest priority)

## 📋 Required Render Secrets

You must set these in your Render Dashboard > Secrets:

### Database
```
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
```

### Redis (if using external Redis service)
```
REDIS_URL=redis://your-redis-host:port/0
```

### Security
```
SECRET_KEY=your-secret-key-here
```

### Email
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SENDGRID_API_KEY=your-sendgrid-key
```

### AI Services
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Optional Services
```
GROQ_API_KEY=your-groq-key
OPENCLAW_API_KEY=your-openclaw-key
```

## ⚠️ Important Notes

1. **Never commit secrets to git** - Use Render Secrets dashboard
2. **Local .env is only for development** - Render secrets override it
3. **Test with Render's environment** - Don't assume local values work
4. **Database URL must include SSL** - Required for external connections

## 🚀 Deployment Commands

Your `start.sh` script already handles:
- Dynamic port binding via `${PORT:-7860}`
- External Redis detection via `REDIS_URL` 
- Proper Celery configuration

## 🔍 Troubleshooting

If deployment fails:

1. **Check Render logs**: Look for "Port scan timeout"
2. **Verify secrets**: Ensure all required secrets are set
3. **Test database**: Check if DATABASE_URL is accessible
4. **Redis connection**: Verify REDIS_URL format is correct

## 📝 Example Render Environment

```bash
# Render provides these automatically
PORT=10000
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://external-redis:6379/0

# Your app will use these instead of .env values
```

This ensures your deployment works consistently across environments!
