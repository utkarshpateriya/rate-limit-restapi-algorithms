import uvicorn
from fastapi import FastAPI, Query
from middleware import RateLimitMiddleware, EndpointRateLimitMiddleware
from rate_limiters import (
    FixedWindowCounter,
    SlidingWindowLog,
    SlidingWindowCounter,
    TokenBucket,
    LeakyBucket,
)

app = FastAPI(
    title="Rate Limiting Examples for RESTful APIs",
    description="""
    This project demonstrates various rate limiting strategies for RESTful APIs using FastAPI.
    
    ## Rate Limiting Algorithms Demonstrated:
    
    1. **Fixed Window Counter** - Divides time into fixed windows. Simple but has edge case issues at boundaries.
    2. **Sliding Window Log** - Maintains a log of request timestamps. Most accurate but memory intensive.
    3. **Sliding Window Counter** - Hybrid approach combining fixed and sliding window concepts.
    4. **Token Bucket** - Tokens added at fixed rate. Allows burst traffic while maintaining average rate limit.
    5. **Leaky Bucket** - Requests processed at fixed rate. Smooths out traffic and prevents bursts.
    """,
    version="1.0.0"
)

# Initialize different rate limiters
fixed_window = FixedWindowCounter(window_size=60, max_requests=10)
sliding_log = SlidingWindowLog(window_size=60, max_requests=10)
sliding_counter = SlidingWindowCounter(window_size=60, max_requests=10)
token_bucket = TokenBucket(capacity=10, refill_rate=2.0)
leaky_bucket = LeakyBucket(capacity=10, leak_rate=2.0)

# Create separate limiters for different endpoints
endpoint_limiters = {
    "/fixed-window": fixed_window,
    "/sliding-window-log": sliding_log,
    "/sliding-window-counter": sliding_counter,
    "/token-bucket": token_bucket,
    "/leaky-bucket": leaky_bucket,
}

# Add middleware with endpoint-specific limiters
app.add_middleware(EndpointRateLimitMiddleware, endpoint_limiters=endpoint_limiters)


# ============================================================================
# Demonstration Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint with API documentation."""
    return {
        "message": "Welcome to Rate Limiting Algorithms API",
        "endpoints": [
            "/fixed-window",
            "/sliding-window-log",
            "/sliding-window-counter",
            "/token-bucket",
            "/leaky-bucket",
            "/global-rate-limit",
            "/info"
        ],
        "docs": "/docs"
    }


@app.get("/fixed-window")
def fixed_window_endpoint():
    """
    Endpoint using Fixed Window Counter algorithm.
    Limit: 10 requests per 60 seconds
    """
    return {
        "algorithm": "Fixed Window Counter",
        "message": "Request successful",
        "description": "Divides time into fixed windows and counts requests in each window."
    }


@app.get("/sliding-window-log")
def sliding_window_log_endpoint():
    """
    Endpoint using Sliding Window Log algorithm.
    Limit: 10 requests per 60 seconds
    """
    return {
        "algorithm": "Sliding Window Log",
        "message": "Request successful",
        "description": "Maintains a log of request timestamps for maximum accuracy."
    }


@app.get("/sliding-window-counter")
def sliding_window_counter_endpoint():
    """
    Endpoint using Sliding Window Counter algorithm.
    Limit: 10 requests per 60 seconds
    """
    return {
        "algorithm": "Sliding Window Counter",
        "message": "Request successful",
        "description": "Hybrid approach combining fixed window and sliding window concepts."
    }


@app.get("/token-bucket")
def token_bucket_endpoint():
    """
    Endpoint using Token Bucket algorithm.
    Capacity: 10 tokens, refill rate: 2 tokens/second
    """
    return {
        "algorithm": "Token Bucket",
        "message": "Request successful",
        "description": "Allows burst traffic while maintaining average rate limit."
    }


@app.get("/leaky-bucket")
def leaky_bucket_endpoint():
    """
    Endpoint using Leaky Bucket algorithm.
    Capacity: 10 requests, leak rate: 2 requests/second
    """
    return {
        "algorithm": "Leaky Bucket",
        "message": "Request successful",
        "description": "Processes requests at fixed rate for smooth traffic flow."
    }


@app.get("/global-rate-limit")
def global_rate_limit():
    """
    Endpoint with global rate limiting using Token Bucket.
    This endpoint is rate limited globally (not included in endpoint_limiters).
    """
    return {
        "algorithm": "Global Token Bucket",
        "message": "Request successful",
        "description": "This endpoint could be protected with global rate limiting."
    }


@app.get("/info")
def get_info(algorithm: str = Query(None, description="Algorithm name to get info for")):
    """
    Get information about rate limiting algorithms.
    
    Query Parameters:
    - algorithm: Optional. Specify which algorithm info to get (default: all)
    """
    algorithms = {
        "Fixed Window Counter": {
            "pros": ["Simple to implement", "Low memory overhead"],
            "cons": ["Boundary issues", "Uneven request distribution"],
            "use_case": "When simplicity is preferred over accuracy"
        },
        "Sliding Window Log": {
            "pros": ["Highly accurate", "No boundary issues"],
            "cons": ["High memory overhead", "Complex implementation"],
            "use_case": "When accuracy is critical and memory is not a constraint"
        },
        "Sliding Window Counter": {
            "pros": ["Balanced accuracy", "Lower memory than log"],
            "cons": ["Slightly less accurate than log"],
            "use_case": "General purpose rate limiting with good memory efficiency"
        },
        "Token Bucket": {
            "pros": ["Allows burst traffic", "Flexible capacity"],
            "cons": ["More complex", "Requires continuous refill calculation"],
            "use_case": "When you want to allow burst traffic while maintaining average limit"
        },
        "Leaky Bucket": {
            "pros": ["Smooth traffic flow", "Prevents bursts"],
            "cons": ["May not allow legitimate bursts", "More memory intensive"],
            "use_case": "When you need smooth, predictable traffic flow"
        }
    }

    if algorithm and algorithm in algorithms:
        return {algorithm: algorithms[algorithm]}
    
    return algorithms


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint (not rate limited)."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)