# Troubleshooting Guide

## Common Issues

### Backend Issues

#### Database Connection Refused
**Symptom**: `Connection refused` error

**Solution**:
1. Ensure PostgreSQL is running: `docker-compose ps postgres`
2. Check connection string in `.env`
3. Verify database exists: `psql -U postgres -l`

#### Ollama Not Responding
**Symptom**: `Connection refused` on AI endpoints

**Solution**:
1. Start Ollama: `ollama serve`
2. Pull model: `ollama pull qwen2.5`
3. Check model list: `ollama list`

#### Memory Errors
**Symptom**: `MemoryError` or slow responses

**Solution**:
1. Check available memory: `free -h`
2. Reduce batch size in settings
3. Restart backend service

### Frontend Issues

#### Build Failures
**Symptom**: `npm run build` fails

**Solution**:
1. Clear cache: `rm -rf node_modules .next`
2. Reinstall: `npm install`
3. Check TypeScript errors: `npm run typecheck`

#### API Connection Errors
**Symptom**: Network errors in browser console

**Solution**:
1. Verify backend is running
2. Check CORS settings
3. Verify API URL in environment

### Workflow Issues

#### Workflow Stuck
**Symptom**: Workflow not progressing

**Solution**:
1. Check workflow status in monitoring
2. Review execution logs
3. Restart workflow if needed

#### Agent Timeout
**Symptom**: Agent task timeout

**Solution**:
1. Check agent health
2. Increase timeout in settings
3. Verify Ollama is responsive

### Performance Issues

#### Slow Queries
**Symptom**: High response times

**Solution**:
1. Check database indexes
2. Review slow query log
3. Optimize queries

#### High Memory Usage
**Symptom**: Application consuming too much memory

**Solution**:
1. Check for memory leaks
2. Restart services
3. Increase memory limits

## Debug Mode

Enable debug mode:
```env
DEBUG_MODE=true
API_LOGGING=true
```

## Logs

View logs:
```bash
# Docker
docker-compose logs -f backend

# Local
tail -f logs/app.log
```

## Getting Help

- Check [FAQ](./FAQ.md)
- Search [Issues](https://github.com/forgeai/forgeai/issues)
- Join [Discord](https://discord.gg/forgeai)
