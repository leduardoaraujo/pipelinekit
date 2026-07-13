import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from forgeflow.pipeline.executor import PipelineExecutor
from forgeflow.pipeline.loader import PipelineLoader

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

app = FastAPI(
    title="ForgeFlow",
    description="Central de APIs padronizada para ingestão e distribuição de dados",
    version="0.1.0",
)

logger = structlog.get_logger()


class PipelineRunRequest(BaseModel):
    pipeline_name: str


@app.get("/")
async def root():
    return {
        "name": "ForgeFlow",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/pipelines")
async def list_pipelines():
    try:
        pipelines = PipelineLoader.load_from_file("config/pipelines.yaml")
        return {
            "count": len(pipelines),
            "pipelines": [
                {
                    "name": p["name"],
                    "enabled": p.get("enabled", True),
                    "connector": p["connector"]["type"],
                    "transformer": p["transformer"]["type"],
                    "sinks": [s["type"] for s in p["sinks"]],
                }
                for p in pipelines
            ],
        }
    except Exception as e:
        logger.error("list_pipelines_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipelines/run")
async def run_pipeline(request: PipelineRunRequest):
    try:
        pipelines = PipelineLoader.load_from_file("config/pipelines.yaml")
        pipeline = next(
            (p for p in pipelines if p["name"] == request.pipeline_name), None
        )

        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        PipelineLoader.validate_pipeline(pipeline)

        executor = PipelineExecutor()
        await executor.execute(pipeline)

        return {"status": "success", "pipeline": request.pipeline_name}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("run_pipeline_failed", pipeline=request.pipeline_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}
