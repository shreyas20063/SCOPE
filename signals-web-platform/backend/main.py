"""
FastAPI Backend for Signals & Systems Web Platform

Optimized for 100 concurrent users with:
- WebSocket real-time updates
- In-memory caching (LRU with TTL)
- Rate limiting (per-IP and global)
- Performance monitoring
- Security headers
"""

import time
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import io
import csv

from config import CORS_SETTINGS, API_PREFIX
from core.executor import SimulationExecutor
from core.data_handler import DataHandler
from simulations.catalog import (
    get_all_simulations,
    get_simulation_by_id,
    get_categories,
    get_simulations_by_category,
)
from simulations import get_simulator_class

from utils import (
    websocket_manager,
    simulation_cache,
    get_cached_result,
    cache_result,
    rate_limiter,
    RateLimitExceeded,
    monitor,
    log_request,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting Signals & Systems Backend v2.0...")
    logger.info(f"Cache: max_size={simulation_cache.max_size}, TTL={simulation_cache.ttl_seconds}s")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    logger.info("Shutting down...")
    cleanup_task.cancel()

    # Close all WebSocket connections
    await websocket_manager.close_all()

    # Close monitor log file
    monitor.close()

    await asyncio.sleep(2)
    logger.info("Shutdown complete")


async def periodic_cleanup():
    """Background task for periodic cleanup."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            simulation_cache.cleanup_expired()
            logger.debug("Periodic cleanup completed")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Signals & Systems Simulation Platform",
    description="High-performance web platform for interactive signal processing simulations",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS (public access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    start_time = time.time()

    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Calculate duration and log
    duration_ms = (time.time() - start_time) * 1000

    # Log request (skip health checks)
    if not request.url.path.endswith("/health"):
        client_ip = request.client.host if request.client else "unknown"
        log_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )

    return response


# Rate limiting middleware - DISABLED
# For educational simulations, rate limiting isn't needed.
# Enable this if deploying publicly and experiencing abuse.
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     if request.url.path.endswith("/health"):
#         return await call_next(request)
#     client_ip = request.client.host if request.client else "127.0.0.1"
#     allowed, retry_after = rate_limiter.check_rate_limit(client_ip)
#     if not allowed:
#         return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
#     return await call_next(request)


# Initialize executor
executor = SimulationExecutor(timeout=30)

# Active simulator instances
active_simulators: Dict[str, Any] = {}


def get_or_create_simulator(sim_id: str):
    """Get existing simulator instance or create a new one."""
    simulator_class = get_simulator_class(sim_id)
    if simulator_class is None:
        return None

    if sim_id not in active_simulators:
        simulator = simulator_class(sim_id)
        simulator.initialize()
        active_simulators[sim_id] = simulator

    return active_simulators[sim_id]


def get_cached_or_compute(sim_id: str, params: Dict[str, Any], simulator) -> Dict:
    """Get cached result or compute new one."""
    cached = get_cached_result(sim_id, params)
    if cached is not None:
        monitor.cache_hits += 1
        return {"success": True, "data": cached, "cache_hit": True}

    monitor.cache_misses += 1
    result = executor.execute(simulator.get_state)

    if result["success"]:
        serialized = DataHandler.serialize_result(result["data"])
        cache_result(sim_id, params, serialized)
        return {"success": True, "data": serialized, "cache_hit": False}

    return {"success": False, "error": result.get("error"), "cache_hit": False}


# Request/Response models
class ExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}


class UpdateRequest(BaseModel):
    params: Dict[str, Any]


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check():
    """Detailed readiness check."""
    return {
        "status": "ready",
        "uptime_seconds": round(monitor.uptime_seconds, 2),
        "cache_size": simulation_cache.size,
        "cache_hit_rate": f"{simulation_cache.hit_rate * 100:.1f}%",
        "ws_connections": websocket_manager.connection_count,
        "active_simulators": len(active_simulators),
    }


# ============================================================================
# ANALYTICS ENDPOINT
# ============================================================================

@app.get(f"{API_PREFIX}/analytics")
async def get_analytics():
    """Performance analytics for research papers."""
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "performance": monitor.get_stats(),
        "cache": simulation_cache.get_stats(),
        "rate_limiter": rate_limiter.get_stats(),
        "websocket": websocket_manager.get_stats(),
    }


# ============================================================================
# CATALOG ENDPOINTS (with HTTP caching)
# ============================================================================

@app.get(f"{API_PREFIX}/simulations")
async def list_simulations(category: Optional[str] = None):
    """List simulations (1 hour cache)."""
    if category:
        simulations = get_simulations_by_category(category)
    else:
        simulations = get_all_simulations()

    response = JSONResponse(content=simulations)
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get(f"{API_PREFIX}/simulations/{{sim_id}}")
async def get_simulation(sim_id: str):
    """Get simulation by ID (1 hour cache)."""
    simulation = get_simulation_by_id(sim_id)
    if simulation is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    response = JSONResponse(content=simulation)
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get(f"{API_PREFIX}/categories")
async def list_categories():
    """List categories (1 hour cache)."""
    categories = get_categories()
    response = JSONResponse(content=categories)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


# ============================================================================
# SIMULATION STATE ENDPOINTS
# ============================================================================

@app.get(f"{API_PREFIX}/simulations/{{sim_id}}/state")
async def get_simulation_state(sim_id: str):
    """Get simulation state (with caching)."""
    simulator = get_or_create_simulator(sim_id)

    if simulator is None:
        simulation = get_simulation_by_id(sim_id)
        if simulation is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return {
            "success": True,
            "data": {
                "parameters": simulation.get("default_params", {}),
                "plots": [],
            },
        }

    current_params = getattr(simulator, 'parameters', {})
    result = get_cached_or_compute(sim_id, current_params, simulator)

    if result["success"]:
        return {
            "success": True,
            "data": result["data"],
            "cache_hit": result.get("cache_hit", False),
        }
    else:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": result.get("error")}
        )


@app.post(f"{API_PREFIX}/simulations/{{sim_id}}/execute")
async def execute_simulation(sim_id: str, request: ExecuteRequest):
    """Execute simulation action."""
    simulator = get_or_create_simulator(sim_id)

    if simulator is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Simulation '{sim_id}' not available"}
        )

    action = request.action.lower()
    params = request.params

    try:
        if action == "init":
            result = executor.execute(simulator.initialize, params)
            if result["success"]:
                result = executor.execute(simulator.get_state)

        elif action == "update":
            for key, value in params.items():
                result = executor.execute(simulator.update_parameter, key, value)
                if not result["success"]:
                    break
            if not params:
                result = executor.execute(simulator.get_state)

        elif action == "run":
            result = executor.execute(simulator.run, params)

        elif action == "reset":
            result = executor.execute(simulator.reset)

        elif action == "advance":
            if hasattr(simulator, 'advance_frame'):
                result = executor.execute(simulator.advance_frame)
            else:
                result = executor.execute(simulator.get_state)

        elif action == "step_forward":
            if hasattr(simulator, 'step_forward'):
                result = executor.execute(simulator.step_forward)
            else:
                result = executor.execute(simulator.get_state)

        elif action == "step_backward":
            if hasattr(simulator, 'step_backward'):
                result = executor.execute(simulator.step_backward)
            else:
                result = executor.execute(simulator.get_state)

        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Unknown action: {action}"}
            )

        if result["success"]:
            serialized = DataHandler.serialize_result(result["data"])
            current_params = getattr(simulator, 'parameters', {})
            cache_result(sim_id, current_params, serialized)

            return {"success": True, "data": serialized}
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": result.get("error")}
            )

    except Exception as e:
        logger.exception(f"Execution error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post(f"{API_PREFIX}/simulations/{{sim_id}}/update")
async def update_simulation(sim_id: str, request: UpdateRequest):
    """Update simulation parameters."""
    simulator = get_or_create_simulator(sim_id)

    if simulator is None:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Simulation '{sim_id}' not found"}
        )

    try:
        for key, value in request.params.items():
            result = executor.execute(simulator.update_parameter, key, value)
            if not result["success"]:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": result.get("error")}
                )

        result = executor.execute(simulator.get_state)

        if result["success"]:
            serialized = DataHandler.serialize_result(result["data"])
            current_params = getattr(simulator, 'parameters', {})
            cache_result(sim_id, current_params, serialized)

            return {"success": True, "data": serialized}
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": result.get("error")}
            )

    except Exception as e:
        logger.exception(f"Update error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# EXPORT ENDPOINT
# ============================================================================

@app.get(f"{API_PREFIX}/simulations/{{sim_id}}/export/csv")
async def export_csv(sim_id: str):
    """Export simulation data as CSV."""
    simulator = get_or_create_simulator(sim_id)

    if simulator is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    try:
        # Get export data from simulator
        if hasattr(simulator, 'get_export_data'):
            export_data = simulator.get_export_data()
        else:
            # Fallback: get current state and extract plot data
            result = executor.execute(simulator.get_state)
            if not result["success"]:
                raise HTTPException(status_code=500, detail="Failed to get simulation state")

            state = result["data"]
            export_data = {
                "headers": [],
                "rows": [],
            }

            # Try to extract data from plots
            for plot in state.get("plots", []):
                if "data" in plot:
                    for trace in plot["data"]:
                        x_data = trace.get("x", [])
                        y_data = trace.get("y", [])
                        name = trace.get("name", "data")

                        if not export_data["headers"]:
                            export_data["headers"] = ["index", f"{name}_x", f"{name}_y"]
                            export_data["rows"] = [
                                [i, x_data[i] if i < len(x_data) else "",
                                 y_data[i] if i < len(y_data) else ""]
                                for i in range(max(len(x_data), len(y_data)))
                            ]
                        else:
                            # Add more columns for additional traces
                            export_data["headers"].extend([f"{name}_x", f"{name}_y"])
                            for i, row in enumerate(export_data["rows"]):
                                row.extend([
                                    x_data[i] if i < len(x_data) else "",
                                    y_data[i] if i < len(y_data) else ""
                                ])

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(export_data.get("headers", []))

        # Write data rows
        for row in export_data.get("rows", []):
            writer.writerow(row)

        output.seek(0)

        # Return as downloadable CSV
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={sim_id}_data.csv"
            }
        )

    except Exception as e:
        logger.exception(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket(f"{API_PREFIX}/simulations/{{sim_id}}/ws")
async def websocket_simulation(websocket: WebSocket, sim_id: str):
    """WebSocket for real-time updates."""
    conn_info = await websocket_manager.connect(sim_id, websocket)
    monitor.ws_connections = websocket_manager.connection_count

    simulator = get_or_create_simulator(sim_id)

    if simulator is None:
        await websocket.send_json({
            "success": False,
            "error": f"Simulation '{sim_id}' not found",
            "type": "error"
        })
        await websocket.close()
        return

    # Send initial state
    try:
        result = executor.execute(simulator.get_state)
        if result["success"]:
            data = DataHandler.serialize_result(result["data"])
            await websocket.send_json({
                "success": True,
                "plots": data.get("plots", []),
                "parameters": data.get("parameters", {}),
                "type": "initial",
            })
    except Exception as e:
        await websocket.send_json({
            "success": False,
            "error": str(e),
            "type": "error"
        })

    # Handle messages
    try:
        while True:
            data = await websocket.receive_json()

            # Rate limit check
            if not websocket_manager.check_rate_limit(conn_info):
                await websocket.send_json({
                    "success": False,
                    "error": "Rate limit exceeded (max 10 msg/sec)",
                    "type": "error",
                })
                continue

            action = data.get("action", "update")
            params = data.get("params", {})

            try:
                if action == "update":
                    for key, value in params.items():
                        result = executor.execute(simulator.update_parameter, key, value)
                        if not result["success"]:
                            await websocket.send_json({
                                "success": False,
                                "error": result.get("error"),
                                "type": "error",
                            })
                            continue

                    result = executor.execute(simulator.get_state)
                    if result["success"]:
                        state = DataHandler.serialize_result(result["data"])
                        current_params = getattr(simulator, 'parameters', {})
                        cache_result(sim_id, current_params, state)

                        await websocket.send_json({
                            "success": True,
                            "plots": state.get("plots", []),
                            "parameters": state.get("parameters", {}),
                            "type": "update",
                        })
                    else:
                        await websocket.send_json({
                            "success": False,
                            "error": result.get("error"),
                            "type": "error",
                        })

                elif action == "reset":
                    result = executor.execute(simulator.reset)
                    if result["success"]:
                        state = DataHandler.serialize_result(result["data"])
                        await websocket.send_json({
                            "success": True,
                            "plots": state.get("plots", []),
                            "parameters": state.get("parameters", {}),
                            "type": "reset",
                        })
                    else:
                        await websocket.send_json({
                            "success": False,
                            "error": result.get("error"),
                            "type": "error",
                        })

                elif action == "ping":
                    await websocket.send_json({"success": True, "type": "pong"})

                else:
                    await websocket.send_json({
                        "success": False,
                        "error": f"Unknown action: {action}",
                        "type": "error",
                    })

            except Exception as e:
                logger.warning(f"WebSocket error: {e}")
                await websocket.send_json({
                    "success": False,
                    "error": str(e),
                    "type": "error",
                })

    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(sim_id, conn_info)
        monitor.ws_connections = websocket_manager.connection_count


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Signals & Systems Simulation Platform API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Real-time WebSocket updates",
            "In-memory caching (LRU)",
            "Rate limiting",
            "Performance monitoring",
        ],
        "endpoints": {
            "health": "/health",
            "ready": "/health/ready",
            "analytics": f"{API_PREFIX}/analytics",
            "simulations": f"{API_PREFIX}/simulations",
            "websocket": f"ws://host{API_PREFIX}/simulations/{{sim_id}}/ws",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
    )
