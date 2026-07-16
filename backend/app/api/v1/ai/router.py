"""AI API router."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.ai.schemas.chat import ChatRequest, ChatResponse, ConversationHistory
from app.ai.schemas.model import ModelListResponse, ModelSwitchRequest, ModelSwitchResponse, OllamaStatus
from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=BaseResponse[ChatResponse])
async def chat(
    request: ChatRequest, req: Request
) -> BaseResponse[ChatResponse]:
    """Send a chat message and receive a complete response."""
    controller = req.app.state.chat_controller
    result = await controller.chat(request)
    return BaseResponse(data=result)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """Send a chat message and stream the response as server-sent events."""
    controller = req.app.state.chat_controller

    async def event_generator():
        async for chunk in controller.chat_stream(request):
            data = chunk.model_dump_json()
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models", response_model=BaseResponse[ModelListResponse])
async def list_models(req: Request) -> BaseResponse[ModelListResponse]:
    """List available AI models."""
    controller = req.app.state.chat_controller
    result = await controller.get_models()
    return BaseResponse(data=result)


@router.post("/models/switch", response_model=BaseResponse[ModelSwitchResponse])
async def switch_model(
    request: ModelSwitchRequest, req: Request
) -> BaseResponse[ModelSwitchResponse]:
    """Switch the active AI model."""
    controller = req.app.state.chat_controller
    result = await controller.switch_model(request.model_name)
    return BaseResponse(data=result)


@router.get("/status", response_model=BaseResponse[OllamaStatus])
async def get_status(req: Request) -> BaseResponse[OllamaStatus]:
    """Get Ollama and model status."""
    controller = req.app.state.chat_controller
    result = await controller.get_status()
    return BaseResponse(data=result)


@router.post("/stop", response_model=BaseResponse[dict])
async def stop_generation(
    conversation_id: str, req: Request
) -> BaseResponse[dict]:
    """Stop an active generation."""
    controller = req.app.state.chat_controller
    stopped = await controller.stop_generation(conversation_id)
    return BaseResponse(
        data={"stopped": stopped, "conversation_id": conversation_id}
    )


@router.get("/conversations", response_model=BaseResponse[list[ConversationHistory]])
async def list_conversations(req: Request) -> BaseResponse[list[ConversationHistory]]:
    """List all conversations."""
    manager = req.app.state.conversation_manager
    conversations = manager.list_conversations()
    return BaseResponse(data=conversations)


@router.post("/conversations", response_model=BaseResponse[ConversationHistory])
async def create_conversation(
    model: str | None = None, req: Request = None
) -> BaseResponse[ConversationHistory]:
    """Create a new conversation."""
    manager = req.app.state.conversation_manager
    active_model = model or req.app.state.settings.DEFAULT_MODEL
    conversation = manager.create_conversation(active_model)
    return BaseResponse(data=conversation)


@router.get(
    "/conversations/{conversation_id}",
    response_model=BaseResponse[ConversationHistory],
)
async def get_conversation(
    conversation_id: str, req: Request
) -> BaseResponse[ConversationHistory]:
    """Get a conversation by ID."""
    manager = req.app.state.conversation_manager
    conversation = manager.get_conversation(conversation_id)
    return BaseResponse(data=conversation)


@router.delete("/conversations/{conversation_id}", response_model=BaseResponse[dict])
async def delete_conversation(
    conversation_id: str, req: Request
) -> BaseResponse[dict]:
    """Delete a conversation."""
    manager = req.app.state.conversation_manager
    deleted = manager.delete_conversation(conversation_id)
    return BaseResponse(
        data={"deleted": deleted, "conversation_id": conversation_id}
    )


@router.post("/prompts", response_model=BaseResponse[list[dict[str, str]]])
async def list_prompts(req: Request) -> BaseResponse[list[dict[str, str]]]:
    """List available prompt templates."""
    registry = req.app.state.prompt_registry
    prompts = registry.list_prompts()
    return BaseResponse(data=prompts)
